from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_wrapper import wrap_function_wrapper

from newrelic.hooks.framework_tornado import retrieve_current_transaction


def template_generate_wrapper(wrapped, instance, args, kwargs):
    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    with FunctionTrace(transaction, name=instance.name,
            group='Template/Render'):
        return wrapped(*args, **kwargs)


def template_generate_python_wrapper(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    if result is not None:
        return ('import newrelic.api.function_trace as _nr_fxn_trace\n'
                'import newrelic.api.transaction as _nr_txn\n'
                ) + result


def block_generate_wrapper(wrapped, instance, args, kwargs):

    def execute(writer, *args, **kwargs):
        if not hasattr(instance, 'line'):
            return wrapped(writer, *args, **kwargs)

        writer.write_line('with _nr_fxn_trace.FunctionTrace('
                '_nr_txn.current_transaction(), name=%r, '
                'group="Template/Block"):' % instance.name, instance.line)

        with writer.indent():
            writer.write_line("pass", instance.line)
            return wrapped(writer, *args, **kwargs)

    return execute(*args, **kwargs)


def instrument_tornado_template(module):
    wrap_function_wrapper(module, 'Template.generate',
            template_generate_wrapper)
    wrap_function_wrapper(module, 'Template._generate_python',
            template_generate_python_wrapper)
    wrap_function_wrapper(module, '_NamedBlock.generate',
            block_generate_wrapper)
