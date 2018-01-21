from newrelic.config import (
        initialize as __initialize,
        extra_settings as __extra_settings)
from newrelic.core.config import (
        global_settings as __global_settings,
        ignore_status_code as __ignore_status_code)

from newrelic.core.agent import (
        shutdown_agent as __shutdown_agent,
        register_data_source as __register_data_source)

from newrelic.samplers.decorators import (
        data_source_generator as __data_source_generator,
        data_source_factory as __data_source_factory)

from newrelic.api.application import (
        application_instance as __application,
        register_application as __register_application,
        application_settings as __application_settings)

from newrelic.api.transaction import (
        current_transaction as __current_transaction,
        set_transaction_name as __set_transaction_name,
        end_of_transaction as __end_of_transaction,
        set_background_task as __set_background_task,
        ignore_transaction as __ignore_transaction,
        suppress_apdex_metric as __suppress_apdex_metric,
        capture_request_params as __capture_request_params,
        add_custom_parameter as __add_custom_parameter,
        add_framework_info as __add_framework_info,
        record_exception as __record_exception,
        get_browser_timing_header as __get_browser_timing_header,
        get_browser_timing_footer as __get_browser_timing_footer,
        disable_browser_autorum as __disable_browser_autorum,
        suppress_transaction_trace as __suppress_transaction_trace,
        record_custom_metric as __record_custom_metric,
        record_custom_metrics as __record_custom_metrics,
        record_custom_event as __record_custom_event)

from newrelic.api.transaction_context import (
        TransactionContext as __TransactionContext)

# DEPRECATED - The name_transaction call is deprecated and the
# set_transaction_name function should be used instead.

from newrelic.api.transaction import name_transaction as __name_transaction

# DEPRECATED - The add_user_attribute call is deprecated and the
# add_custom_parameter function should be used instead.

from newrelic.api.transaction import add_user_attribute as __add_user_attribute

from newrelic.api.web_transaction import (
        wsgi_application as __wsgi_application,
        WebTransaction as __WebTransaction,
        WSGIApplicationWrapper as __WSGIApplicationWrapper,
        wrap_wsgi_application as __wrap_wsgi_application)

from newrelic.api.background_task import (
        background_task as __background_task,
        BackgroundTask as __BackgroundTask,
        BackgroundTaskWrapper as __BackgroundTaskWrapper,
        wrap_background_task as __wrap_background_task)

from newrelic.api.transaction_name import (
        transaction_name as __transaction_name,
        TransactionNameWrapper as __TransactionNameWrapper,
        wrap_transaction_name as __wrap_transaction_name)

from newrelic.api.function_trace import (
        function_trace as __function_trace,
        FunctionTrace as __FunctionTrace,
        FunctionTraceWrapper as __FunctionTraceWrapper,
        wrap_function_trace as __wrap_function_trace)

# EXPERIMENTAL - Generator traces are currently experimental and may not
# exist in this form in future versions of the agent.

from newrelic.api.generator_trace import (
        generator_trace as __generator_trace,
        GeneratorTraceWrapper as __GeneratorTraceWrapper,
        wrap_generator_trace as __wrap_generator_trace)

# EXPERIMENTAL - Profile traces are currently experimental and may not
# exist in this form in future versions of the agent.

from newrelic.api.profile_trace import (
        profile_trace as __profile_trace,
        ProfileTraceWrapper as __ProfileTraceWrapper,
        wrap_profile_trace as __wrap_profile_trace)

from newrelic.api.database_trace import (
        database_trace as __database_trace,
        DatabaseTrace as __DatabaseTrace,
        DatabaseTraceWrapper as __DatabaseTraceWrapper,
        wrap_database_trace as __wrap_database_trace,
        register_database_client as __register_database_client)

from newrelic.api.datastore_trace import (
        datastore_trace as __datastore_trace,
        DatastoreTrace as __DatastoreTrace,
        DatastoreTraceWrapper as __DatastoreTraceWrapper,
        wrap_datastore_trace as __wrap_datastore_trace)

from newrelic.api.external_trace import (
        external_trace as __external_trace,
        ExternalTrace as __ExternalTrace,
        ExternalTraceWrapper as __ExternalTraceWrapper,
        wrap_external_trace as __wrap_external_trace)

from newrelic.api.error_trace import (
        error_trace as __error_trace,
        ErrorTrace as __ErrorTrace,
        ErrorTraceWrapper as __ErrorTraceWrapper,
        wrap_error_trace as __wrap_error_trace)

from newrelic.api.message_trace import (
        message_trace as __message_trace,
        MessageTrace as __MessageTrace,
        MessageTraceWrapper as __MessageTraceWrapper,
        wrap_message_trace as __wrap_message_trace)

from newrelic.api.message_transaction import (
        message_transaction as __message_transaction,
        MessageTransaction as __MessageTransaction,
        MessageTransactionWrapper as __MessageTransactionWrapper,
        wrap_message_transaction as __wrap_message_transaction)

from newrelic.common.object_names import callable_name as __callable_name

from newrelic.common.object_wrapper import (
        ObjectProxy as __ObjectProxy,
        wrap_object as __wrap_object,
        wrap_object_attribute as __wrap_object_attribute,
        resolve_path as __resolve_path,
        transient_function_wrapper as __transient_function_wrapper,
        FunctionWrapper as __FunctionWrapper,
        function_wrapper as __function_wrapper,
        wrap_function_wrapper as __wrap_function_wrapper,
        patch_function_wrapper as __patch_function_wrapper,
        ObjectWrapper as __ObjectWrapper,
        wrap_callable as __wrap_callable,
        pre_function as __pre_function,
        PreFunctionWrapper as __PreFunctionWrapper,
        wrap_pre_function as __wrap_pre_function,
        post_function as __post_function,
        PostFunctionWrapper as __PostFunctionWrapper,
        wrap_post_function as __wrap_post_function,
        in_function as __in_function,
        InFunctionWrapper as __InFunctionWrapper,
        wrap_in_function as __wrap_in_function,
        out_function as __out_function,
        OutFunctionWrapper as __OutFunctionWrapper,
        wrap_out_function as __wrap_out_function)

from newrelic.api.html_insertion import (
        insert_html_snippet as __insert_html_snippet,
        verify_body_exists as __verify_body_exists)

from newrelic.api.supportability import wrap_api_call as __wrap_api_call

initialize = __initialize
extra_settings = __wrap_api_call(__extra_settings,
        'extra_settings')
global_settings = __wrap_api_call(__global_settings,
        'global_settings')
ignore_status_code = __wrap_api_call(__ignore_status_code,
        'ignore_status_code')
shutdown_agent = __wrap_api_call(__shutdown_agent,
        'shutdown_agent')
register_data_source = __wrap_api_call(__register_data_source,
        'register_data_source')
data_source_generator = __wrap_api_call(__data_source_generator,
        'data_source_generator')
data_source_factory = __wrap_api_call(__data_source_factory,
        'data_source_factory')
application = __wrap_api_call(__application,
        'application')
register_application = __register_application
application_settings = __wrap_api_call(__application_settings,
        'application_settings')
current_transaction = __wrap_api_call(__current_transaction,
        'current_transaction')
set_transaction_name = __wrap_api_call(__set_transaction_name,
        'set_transaction_name')
end_of_transaction = __wrap_api_call(__end_of_transaction,
        'end_of_transaction')
set_background_task = __wrap_api_call(__set_background_task,
        'set_background_task')
ignore_transaction = __wrap_api_call(__ignore_transaction,
        'ignore_transaction')
suppress_apdex_metric = __wrap_api_call(__suppress_apdex_metric,
        'suppress_apdex_metric')
capture_request_params = __wrap_api_call(__capture_request_params,
        'capture_request_params')
add_custom_parameter = __wrap_api_call(__add_custom_parameter,
        'add_custom_parameter')
add_framework_info = __wrap_api_call(__add_framework_info,
        'add_framework_info')
record_exception = __wrap_api_call(__record_exception,
        'record_exception')
get_browser_timing_header = __wrap_api_call(__get_browser_timing_header,
        'get_browser_timing_header')
get_browser_timing_footer = __wrap_api_call(__get_browser_timing_footer,
        'get_browser_timing_footer')
disable_browser_autorum = __wrap_api_call(__disable_browser_autorum,
        'disable_browser_autorum')
suppress_transaction_trace = __wrap_api_call(__suppress_transaction_trace,
        'suppress_transaction_trace')
record_custom_metric = __wrap_api_call(__record_custom_metric,
        'record_custom_metric')
record_custom_metrics = __wrap_api_call(__record_custom_metrics,
        'record_custom_metrics')
record_custom_event = __wrap_api_call(__record_custom_event,
        'record_custom_event')
TransactionContext = __wrap_api_call(__TransactionContext,
        'TransactionContext')
name_transaction = __wrap_api_call(__name_transaction,
        'name_transaction')
add_user_attribute = __wrap_api_call(__add_user_attribute,
        'add_user_attribute')
wsgi_application = __wsgi_application
WebTransaction = __wrap_api_call(__WebTransaction,
        'WebTransaction')
WSGIApplicationWrapper = __WSGIApplicationWrapper
wrap_wsgi_application = __wrap_wsgi_application
background_task = __wrap_api_call(__background_task,
        'background_task')
BackgroundTask = __wrap_api_call(__BackgroundTask,
        'BackgroundTask')
BackgroundTaskWrapper = __wrap_api_call(__BackgroundTaskWrapper,
        'BackgroundTaskWrapper')
wrap_background_task = __wrap_api_call(__wrap_background_task,
        'wrap_background_task')
transaction_name = __wrap_api_call(__transaction_name,
        'transaction_name')
TransactionNameWrapper = __wrap_api_call(__TransactionNameWrapper,
        'TransactionNameWrapper')
wrap_transaction_name = __wrap_api_call(__wrap_transaction_name,
        'wrap_transaction_name')
function_trace = __wrap_api_call(__function_trace,
        'function_trace')
FunctionTrace = __wrap_api_call(__FunctionTrace,
        'FunctionTrace')
FunctionTraceWrapper = __wrap_api_call(__FunctionTraceWrapper,
        'FunctionTraceWrapper')
wrap_function_trace = __wrap_api_call(__wrap_function_trace,
        'wrap_function_trace')
generator_trace = __wrap_api_call(__generator_trace,
        'generator_trace')
GeneratorTraceWrapper = __wrap_api_call(__GeneratorTraceWrapper,
        'GeneratorTraceWrapper')
wrap_generator_trace = __wrap_api_call(__wrap_generator_trace,
        'wrap_generator_trace')
profile_trace = __wrap_api_call(__profile_trace,
        'profile_trace')
ProfileTraceWrapper = __wrap_api_call(__ProfileTraceWrapper,
        'ProfileTraceWrapper')
wrap_profile_trace = __wrap_api_call(__wrap_profile_trace,
        'wrap_profile_trace')
database_trace = __wrap_api_call(__database_trace,
        'database_trace')
DatabaseTrace = __wrap_api_call(__DatabaseTrace,
        'DatabaseTrace')
DatabaseTraceWrapper = __wrap_api_call(__DatabaseTraceWrapper,
        'DatabaseTraceWrapper')
wrap_database_trace = __wrap_api_call(__wrap_database_trace,
        'wrap_database_trace')
register_database_client = __wrap_api_call(__register_database_client,
        'register_database_client')
datastore_trace = __wrap_api_call(__datastore_trace,
        'datastore_trace')
DatastoreTrace = __wrap_api_call(__DatastoreTrace,
        'DatastoreTrace')
DatastoreTraceWrapper = __wrap_api_call(__DatastoreTraceWrapper,
        'DatastoreTraceWrapper')
wrap_datastore_trace = __wrap_api_call(__wrap_datastore_trace,
        'wrap_datastore_trace')
external_trace = __wrap_api_call(__external_trace,
        'external_trace')
ExternalTrace = __wrap_api_call(__ExternalTrace,
        'ExternalTrace')
ExternalTraceWrapper = __wrap_api_call(__ExternalTraceWrapper,
        'ExternalTraceWrapper')
wrap_external_trace = __wrap_api_call(__wrap_external_trace,
        'wrap_external_trace')
error_trace = __wrap_api_call(__error_trace,
        'error_trace')
ErrorTrace = __wrap_api_call(__ErrorTrace,
        'ErrorTrace')
ErrorTraceWrapper = __wrap_api_call(__ErrorTraceWrapper,
        'ErrorTraceWrapper')
wrap_error_trace = __wrap_api_call(__wrap_error_trace,
        'wrap_error_trace')
message_trace = __wrap_api_call(__message_trace,
        'message_trace')
MessageTrace = __wrap_api_call(__MessageTrace,
        'MessageTrace')
MessageTraceWrapper = __wrap_api_call(__MessageTraceWrapper,
        'MessageTraceWrapper')
wrap_message_trace = __wrap_api_call(__wrap_message_trace,
        'wrap_message_trace')
message_transaction = __wrap_api_call(__message_transaction,
        'message_trace')
MessageTransaction = __wrap_api_call(__MessageTransaction,
        'MessageTransaction')
MessageTransactionWrapper = __wrap_api_call(__MessageTransactionWrapper,
        'MessageTransactionWrapper')
wrap_message_transaction = __wrap_api_call(__wrap_message_transaction,
        'wrap_message_transaction')
callable_name = __wrap_api_call(__callable_name,
        'callable_name')
ObjectProxy = __wrap_api_call(__ObjectProxy,
        'ObjectProxy')
wrap_object = __wrap_api_call(__wrap_object,
        'wrap_object')
wrap_object_attribute = __wrap_api_call(__wrap_object_attribute,
        'wrap_object_attribute')
resolve_path = __wrap_api_call(__resolve_path,
        'resolve_path')
transient_function_wrapper = __wrap_api_call(__transient_function_wrapper,
        'transient_function_wrapper')
FunctionWrapper = __wrap_api_call(__FunctionWrapper,
        'FunctionWrapper')
function_wrapper = __wrap_api_call(__function_wrapper,
        'function_wrapper')
wrap_function_wrapper = __wrap_api_call(__wrap_function_wrapper,
        'wrap_function_wrapper')
patch_function_wrapper = __wrap_api_call(__patch_function_wrapper,
        'patch_function_wrapper')
ObjectWrapper = __wrap_api_call(__ObjectWrapper,
        'ObjectWrapper')
wrap_callable = __wrap_api_call(__wrap_callable,
        'wrap_callable')
pre_function = __wrap_api_call(__pre_function,
        'pre_function')
PreFunctionWrapper = __wrap_api_call(__PreFunctionWrapper,
        'PreFunctionWrapper')
wrap_pre_function = __wrap_api_call(__wrap_pre_function,
        'wrap_pre_function')
post_function = __wrap_api_call(__post_function,
        'post_function')
PostFunctionWrapper = __wrap_api_call(__PostFunctionWrapper,
        'PostFunctionWrapper')
wrap_post_function = __wrap_api_call(__wrap_post_function,
        'wrap_post_function')
in_function = __wrap_api_call(__in_function,
        'in_function')
InFunctionWrapper = __wrap_api_call(__InFunctionWrapper,
        'InFunctionWrapper')
wrap_in_function = __wrap_api_call(__wrap_in_function,
        'wrap_in_function')
out_function = __wrap_api_call(__out_function,
        'out_function')
OutFunctionWrapper = __wrap_api_call(__OutFunctionWrapper,
        'OutFunctionWrapper')
wrap_out_function = __wrap_api_call(__wrap_out_function,
        'wrap_out_function')
insert_html_snippet = __wrap_api_call(__insert_html_snippet,
        'insert_html_snippet')
verify_body_exists = __wrap_api_call(__verify_body_exists,
        'verify_body_exists')
