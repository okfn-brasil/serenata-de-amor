import functools
import sys

from newrelic.api.application import Application, application_instance
from newrelic.api.transaction import Transaction, current_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object

class BackgroundTask(Transaction):

    def __init__(self, application, name, group=None):

        # Initialise the common transaction base class.

        super(BackgroundTask, self).__init__(application)

        # Mark this as a background task even if disabled.

        self.background_task = True

        # Set async related attributes

        self._ref_count = 0
        self._is_finalized = False
        self._request_handler_finalize = False
        self._server_adapter_finalize = False

        # Bail out if the transaction is running in a
        # disabled state.

        if not self.enabled:
            return

        # Name the web transaction from supplied values.

        self.set_transaction_name(name, group, priority=1)

def BackgroundTaskWrapper(wrapped, application=None, name=None, group=None):

    def wrapper(wrapped, instance, args, kwargs):
        if callable(name):
            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)

        elif name is None:
            _name = callable_name(wrapped)

        else:
            _name = name

        if callable(group):
            if instance is not None:
                _group = group(instance, *args, **kwargs)
            else:
                _group = group(*args, **kwargs)

        else:
            _group = group

        # Check to see if any transaction is present, even an inactive
        # one which has been marked to be ignored or which has been
        # stopped already.

        transaction = current_transaction(active_only=False)

        if transaction:
            # If there is any active transaction we will return without
            # applying a new WSGI application wrapper context. In the
            # case of a transaction which is being ignored or which has
            # been stopped, we do that without doing anything further.

            if transaction.ignore_transaction or transaction.stopped:
                return wrapped(*args, **kwargs)

            # Check to see if we are being called within the context of
            # a web transaction. If we are, then we will just flag the
            # current web transaction as a background task if not
            # already marked as such and name the web transaction as
            # well.

            if type(transaction) == WebTransaction:
                if not transaction.background_task:
                    transaction.background_task = True
                    transaction.set_transaction_name(_name, _group)

            return wrapped(*args, **kwargs)

        # Otherwise treat it as top level transaction.

        if type(application) != Application:
            _application = application_instance(application)
        else:
            _application = application

        try:
            success = True
            manager = BackgroundTask(_application, _name, _group)
            manager.__enter__()
            try:
                return wrapped(*args, **kwargs)
            except: #  Catch all
                success = False
                if not manager.__exit__(*sys.exc_info()):
                    raise
        finally:
            if success and manager._ref_count == 0:
                manager._is_finalized = True
                manager.__exit__(None, None, None)
            else:
                manager._request_handler_finalize = True
                manager._server_adapter_finalize = True

                old_transaction = current_transaction()
                if old_transaction is not None:
                    old_transaction.drop_transaction()

    return FunctionWrapper(wrapped, wrapper)

def background_task(application=None, name=None, group=None):
    return functools.partial(BackgroundTaskWrapper,
            application=application, name=name, group=group)

def wrap_background_task(module, object_path, application=None,
        name=None, group=None):
    wrap_object(module, object_path, BackgroundTaskWrapper,
            (application, name, group))
