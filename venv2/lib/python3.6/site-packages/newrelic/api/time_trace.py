import time
import traceback
import logging

_logger = logging.getLogger(__name__)


class TimeTrace(object):

    node = None

    def __init__(self, transaction):
        self.transaction = transaction
        self.parent = None
        self.child_count = 0
        self.children = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration = 0.0
        self.exclusive = 0.0
        self.activated = False
        self.exited = False
        self.is_async = False
        self.has_async_children = False
        self.min_child_start_time = float('inf')
        self.exc_data = (None, None, None)
        self.should_record_segment_params = False

        if transaction:
            # Don't do further tracing of transaction if
            # it has been explicitly stopped.
            if transaction.stopped:
                self.transaction = None
                return

            self.parent = self.transaction.active_node()

            # parent shall track children immediately
            if (self.parent is not None and
                    not self.parent.terminal_node()):
                self.parent.increment_child_count()

            self.should_record_segment_params = (
                    transaction.should_record_segment_params)

    def __enter__(self):
        if not self.transaction:
            return self

        # Don't do any tracing if parent is designated
        # as a terminal node.

        parent = self.parent

        if not parent or parent.terminal_node():
            self.transaction = None
            self.parent = None
            return parent

        # Record start time.

        self.start_time = time.time()

        # Push ourselves as the current node.

        self.transaction._push_current(self)

        self.activated = True

        return self

    def __exit__(self, exc, value, tb):
        if not self.transaction:
            return

        # Check for violation of context manager protocol where
        # __exit__() is called before __enter__().

        if not self.activated:
            _logger.error('Runtime instrumentation error. The __exit__() '
                    'method of %r was called prior to __enter__() being '
                    'called. Report this issue to New Relic support.\n%s',
                    self, ''.join(traceback.format_stack()[:-1]))

            return

        transaction = self.transaction

        # If recording of time for transaction has already been
        # stopped, then that time has to be used.

        if transaction.stopped:
            self.end_time = transaction.end_time
        else:
            self.end_time = time.time()

        # Ensure end time is greater. Should be unless the
        # system clock has been updated.

        if self.end_time < self.start_time:
            self.end_time = self.start_time

        # Calculate duration and exclusive time. Up till now the
        # exclusive time value had been used to accumulate
        # duration from child nodes as negative value, so just
        # add duration to that to get our own exclusive time.

        self.duration = self.end_time - self.start_time

        self.exclusive += self.duration

        if self.exclusive < 0:
            self.exclusive = 0

        self.exited = True

        self.exc_data = (exc, value, tb)

        # in all cases except async, the children will have exited
        # so this will create the node

        # ----------------------------------------------------------------------
        # SYNC  | The node will be created here. All children will have exited.
        # ----------------------------------------------------------------------
        # Async | The node might be created here (if there are no children).
        #       | Otherwise, this will exit siliently without creating the
        #       | node.
        #       | All references to transaction, parent, exc_data are
        #       | maintained.
        # ----------------------------------------------------------------------
        self.complete_trace()

    def complete_trace(self):
        # we shouldn't continue if we're still running
        if not self.exited:
            return

        # defer node completion until all children have exited
        if len(self.children) != self.child_count:
            return

        # transaction already completed, this is an error
        if self.transaction is None:
            _logger.error('Runtime instrumentation error. The transaction '
                    'already completed meaning a child called complete trace '
                    'after the trace had been finalized. Trace: %r \n%s',
                    self, ''.join(traceback.format_stack()[:-1]))

        # Wipe out transaction reference so can't use object
        # again. Retain reference as local variable for use in
        # this call though.

        transaction = self.transaction
        self.transaction = None

        # Pop ourselves as current node.

        transaction._pop_current(self)

        # wipe out parent too
        parent = self.parent
        self.parent = None

        # wipe out exc data
        exc_data = self.exc_data
        self.exc_data = (None, None, None)

        # Check to see if we're async
        if parent.exited or parent.has_async_children:
            self.is_async = True

        # Give chance for derived class to finalize any data in
        # this object instance. The transaction is passed as a
        # parameter since the transaction object on this instance
        # will have been cleared above.

        self.finalize_data(transaction, *exc_data)

        # Give chance for derived class to create a standin node
        # object to be used in the transaction trace. If we get
        # one then give chance for transaction object to do
        # something with it, as well as our parent node.

        node = self.create_node()

        if node:
            transaction._process_node(node)
            parent.process_child(node)

        # ----------------------------------------------------------------------
        # SYNC  | The parent will not have exited yet, so no node will be
        #       | created. This operation is a NOP.
        # ----------------------------------------------------------------------
        # Async | The parent may have exited already while the child was
        #       | running. If this trace is the last node that's running, this
        #       | complete_trace will create the parent node.
        # ----------------------------------------------------------------------
        parent.complete_trace()

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        pass

    def create_node(self):
        if self.node:
            return self.node(**dict((k, self.__dict__[k])
                    for k in self.node._fields))
        return self

    def terminal_node(self):
        return False

    def update_async_exclusive_time(self, min_child_start_time,
            exclusive_duration):
        # if exited and the child started after, there's no overlap on the
        # exclusive time
        if self.exited and (self.end_time < min_child_start_time):
            exclusive_delta = 0.0
        # else there is overlap and we need to compute it
        elif self.exited:
            exclusive_delta = (self.end_time -
                    min_child_start_time)

            # we don't want to double count the partial exclusive time
            # attributed to this trace, so we should reset the child start time
            # to after this trace ended
            min_child_start_time = self.end_time
        # we're still running so all exclusive duration is taken by us
        else:
            exclusive_delta = exclusive_duration

        # update the exclusive time
        self.exclusive -= exclusive_delta

        # pass any remaining exclusive duration up to the parent
        exclusive_duration_remaining = exclusive_duration - exclusive_delta

        if self.parent and exclusive_duration_remaining > 0.0:
            # call parent exclusive duration delta
            self.parent.update_async_exclusive_time(min_child_start_time,
                    exclusive_duration_remaining)

    def process_child(self, node):
        self.children.append(node)
        if node.is_async:

            # record the lowest start time
            self.min_child_start_time = min(self.min_child_start_time,
                    node.start_time)

            # if there are no children running, finalize exclusive time
            if self.child_count == len(self.children):

                exclusive_duration = node.end_time - self.min_child_start_time

                self.update_async_exclusive_time(self.min_child_start_time,
                        exclusive_duration)

                # reset time range tracking
                self.min_child_start_time = float('inf')
        else:
            self.exclusive -= node.duration

    def increment_child_count(self):
        self.child_count += 1

        # if there's more than 1 child node outstanding
        # then the children are async w.r.t each other
        if (self.child_count - len(self.children)) > 1:
            self.has_async_children = True
        # else, the current trace that's being scheduled is not going to be
        # async. note that this implies that all previous traces have
        # completed
        else:
            self.has_async_children = False
