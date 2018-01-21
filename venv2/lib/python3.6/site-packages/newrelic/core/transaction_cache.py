"""This module implements a global cache for tracking any transactions.

"""

import sys
import threading
import weakref
import traceback
import logging

try:
    import thread
except ImportError:
    import _thread as thread

from newrelic.core.config import global_settings

_logger = logging.getLogger(__name__)

class TransactionCache(object):

    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def current_thread_id(self):
        """Returns the thread ID for the caller.

        When greenlets are present and we detect we are running in the
        greenlet then we use the greenlet ID instead of the thread ID.

        """

        greenlet = sys.modules.get('greenlet')

        if greenlet:
            # Greenlet objects are maintained in a tree structure with
            # the 'parent' attribute pointing to that which a specific
            # instance is associated with. Only the root node has no
            # parent. This node is special and is the one which
            # corresponds to the original thread where the greenlet
            # module was imported and initialised. That root greenlet is
            # never actually running and we should always ignore it. In
            # all other cases where we can obtain a current greenlet,
            # then it should indicate we are running as a greenlet.

            current = greenlet.getcurrent()
            if current is not None and current.parent:
                return id(current)

        return thread.get_ident()

    def current_transaction(self):
        """Return the transaction object if one exists for the currently
        executing thread.

        """

        return self._cache.get(self.current_thread_id())

    def active_threads(self):
        """Returns an iterator over all current stack frames for all
        active threads in the process. The result for each is a tuple
        consisting of the thread identifier, a categorisation of the
        type of thread, and the stack frame. Note that we actually treat
        any greenlets as threads as well. In that case the thread ID is
        the id() of the greenlet.

        This is in this class for convenience as needs to access the
        currently active transactions to categorise transaction threads
        as being for web transactions or background tasks.

        """

        # First yield up those for real Python threads.

        for thread_id, frame in sys._current_frames().items():
            transaction = self._cache.get(thread_id)
            if transaction is not None:
                if transaction.background_task:
                    yield transaction, thread_id, 'BACKGROUND', frame
                else:
                    yield transaction, thread_id, 'REQUEST', frame
            else:
                # Note that there may not always be a thread object.
                # This is because thread could have been created direct
                # against the thread module rather than via the high
                # level threading module. Categorise anything we can't
                # obtain a name for as being 'OTHER'.

                thread = threading._active.get(thread_id)
                if thread is not None and thread.getName().startswith('NR-'):
                    yield None, thread_id, 'AGENT', frame
                else:
                    yield None, thread_id, 'OTHER', frame

        # Now yield up those corresponding to greenlets. Right now only
        # doing this for greenlets in which any active transactions are
        # running. We don't have a way of knowing what non transaction
        # threads are running.

        debug = global_settings().debug

        if debug.enable_coroutine_profiling:
            for thread_id, transaction in self._cache.items():
                if transaction._greenlet is not None:
                    gr = transaction._greenlet()
                    if gr and gr.gr_frame is not None:
                        if transaction.background_task:
                            yield (transaction, thread_id,
                                    'BACKGROUND', gr.gr_frame)
                        else:
                            yield (transaction, thread_id,
                                    'REQUEST', gr.gr_frame)

    def save_transaction(self, transaction):
        """Saves the specified transaction away under the thread ID of
        the current executing thread. Will also cache a reference to the
        greenlet if using coroutines. This is so we can later determine
        the stack trace for a transaction when using greenlets.

        """

        thread_id = transaction.thread_id

        if thread_id in self._cache:
            _logger.error('Runtime instrumentation error. Attempt to '
                    'to save the transaction when one is already saved. '
                    'Report this issue to New Relic support.\n%s',
                    ''.join(traceback.format_stack()[:-1]))

            raise RuntimeError('transaction already active')

        self._cache[thread_id] = transaction

        # We judge whether we are actually running in a coroutine by
        # seeing if the current thread ID is actually listed in the set
        # of all current frames for executing threads. If we are
        # executing within a greenlet, then thread.get_ident() will
        # return the greenlet identifier. This will not be a key in
        # dictionary of all current frames because that will still be
        # the original standard thread which all greenlets are running
        # within.

        transaction._greenlet = None

        if hasattr(sys, '_current_frames'):
            if thread_id not in sys._current_frames():
                greenlet = sys.modules.get('greenlet')
                if greenlet:
                    transaction._greenlet = weakref.ref(greenlet.getcurrent())

    def drop_transaction(self, transaction):
        """Drops the specified transaction, validating that it is
        actually saved away under the current executing thread.

        """

        thread_id = transaction.thread_id

        if not thread_id in self._cache:
            _logger.error('Runtime instrumentation error. Attempt to '
                    'to drop the transaction but where none is active. '
                    'Report this issue to New Relic support.\n%s',
                    ''.join(traceback.format_stack()[:-1]))

            raise RuntimeError('no active transaction')

        current = self._cache.get(thread_id)

        if transaction != current:
            _logger.error('Runtime instrumentation error. Attempt to '
                    'to drop the transaction when it is not the current '
                    'transaction. Report this issue to New Relic support.\n%s',
                    ''.join(traceback.format_stack()[:-1]))

            raise RuntimeError('not the current transaction')

        transaction._greenlet = None

        del self._cache[thread_id]

_transaction_cache = TransactionCache()

def transaction_cache():
    return _transaction_cache
