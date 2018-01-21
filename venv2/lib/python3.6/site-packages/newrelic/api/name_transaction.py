import warnings

from newrelic.api.transaction_name import (transaction_name as name_transaction,
        TransactionNameWrapper as NameTransactionWrapper,
        wrap_transaction_name as wrap_name_transaction)

#warnings.warn('API change. Use transaction_name module instead of '
#       'name_transaction module.', DeprecationWarning, stacklevel=2)
