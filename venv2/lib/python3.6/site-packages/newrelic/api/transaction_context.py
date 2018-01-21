from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import ObjectProxy


class TransactionContext(object):

    def __init__(self, transaction):
        self.transaction = transaction
        self.restore_transaction = None

    def __enter__(self):
        self.restore_transaction = current_transaction(active_only=False)

        if self.restore_transaction:
            self.restore_transaction.drop_transaction()

        if self.transaction:
            self.transaction.save_transaction()

    def __exit__(self, exc, value, tb):
        if self.transaction:
            current = current_transaction(active_only=False)
            if current is self.transaction:
                self.transaction.drop_transaction()

        if self.restore_transaction:
            self.restore_transaction.save_transaction()


class CoroutineTransactionContext(ObjectProxy):
    def __init__(self, coro, transaction):

        self._nr_transaction_context = TransactionContext(transaction)

        # Wrap the coroutine
        super(CoroutineTransactionContext, self).__init__(coro)

    def __iter__(self):
        return self

    def __await__(self):
        return self

    def __next__(self):
        return self.send(None)

    next = __next__

    def send(self, value):
        with self._nr_transaction_context:
            return self.__wrapped__.send(value)

    def throw(self, *args, **kwargs):
        with self._nr_transaction_context:
            return self.__wrapped__.throw(*args, **kwargs)

    def close(self):
        with self._nr_transaction_context:
            return self.__wrapped__.close()
