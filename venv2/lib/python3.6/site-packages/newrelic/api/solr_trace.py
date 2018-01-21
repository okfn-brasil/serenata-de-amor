import newrelic.core.solr_node

import newrelic.api.transaction
import newrelic.api.time_trace
import newrelic.api.object_wrapper


class SolrTrace(newrelic.api.time_trace.TimeTrace):

    node = newrelic.core.solr_node.SolrNode

    def __init__(self, transaction, library, command):
        super(SolrTrace, self).__init__(transaction)

        self.library = library
        self.command = command

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, dict(
                library=self.library, command=self.command))

    def terminal_node(self):
        return True


class SolrTraceWrapper(object):

    def __init__(self, wrapped, library, command):
        if isinstance(wrapped, tuple):
            (instance, wrapped) = wrapped
        else:
            instance = None

        newrelic.api.object_wrapper.update_wrapper(self, wrapped)

        self._nr_instance = instance
        self._nr_next_object = wrapped

        if not hasattr(self, '_nr_last_object'):
            self._nr_last_object = wrapped

        self._nr_library = library
        self._nr_command = command

    def __get__(self, instance, klass):
        if instance is None:
            return self
        descriptor = self._nr_next_object.__get__(instance, klass)
        return self.__class__((instance, descriptor), self._nr_library,
                              self._nr_command)

    def __call__(self, *args, **kwargs):
        transaction = newrelic.api.transaction.current_transaction()
        if not transaction:
            return self._nr_next_object(*args, **kwargs)

        if callable(self._nr_library):
            if self._nr_instance is not None:
                library = self._nr_library(self._nr_instance, *args,
                                           **kwargs)
            else:
                library = self._nr_library(*args, **kwargs)
        else:
            library = self._nr_library

        if callable(self._nr_command):
            if self._nr_instance is not None:
                command = self._nr_command(self._nr_instance, *args,
                                           **kwargs)
            else:
                command = self._nr_command(*args, **kwargs)
        else:
            command = self._nr_command

        with SolrTrace(transaction, library, command):
            return self._nr_next_object(*args, **kwargs)


def solr_trace(library, command):
    def decorator(wrapped):
        return SolrTraceWrapper(wrapped, library, command)
    return decorator


def wrap_solr_trace(module, object_path, library, command):
    newrelic.api.object_wrapper.wrap_object(module, object_path,
            SolrTraceWrapper, (library, command))
