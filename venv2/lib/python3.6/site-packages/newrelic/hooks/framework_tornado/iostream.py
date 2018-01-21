from newrelic.common.object_wrapper import wrap_function_wrapper

def maybe_run_close_callback_wrapper(wrapped, instance, args, kwargs):
    # This will be called when the stream object is closed. It will in
    # turn call a callback we registered in HTTPConnection._on_headers
    # to allow us to finalize the transaction when the socket connection
    # if lost and everythign aborted.

    stream = instance

    if not stream.closed():
        return wrapped(*args, **kwargs)

    if stream._pending_callbacks != 0:
        return wrapped(*args, **kwargs)

    callback = getattr(stream, '_nr_close_callback', None)

    stream._nr_close_callback = None

    if callback:
        callback()

    return wrapped(*args, **kwargs)

def instrument_tornado_iostream(module):

    if hasattr(module, 'BaseIOStream'):
        wrap_function_wrapper(module, 'BaseIOStream._maybe_run_close_callback',
                maybe_run_close_callback_wrapper)

    elif hasattr(module.IOStream, '_maybe_run_close_callback'):
        wrap_function_wrapper(module, 'IOStream._maybe_run_close_callback',
                maybe_run_close_callback_wrapper)
