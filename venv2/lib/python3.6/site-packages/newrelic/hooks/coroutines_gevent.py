from newrelic.api.post_function import wrap_post_function

def _patch_thread(threading=True, *args, **kwargs):
    # This is looking for evidence that are using gevent prior to
    # version 0.13.7. In those versions the threading._sleep() method
    # wasn't being patched, which would result in the agent not working.
    # We do our own patch comparable to what newer versions of gevent
    # are now doing to get things working.

    if threading:
        threading = __import__('threading')
        if hasattr(threading, '_sleep'):
            from gevent.hub import sleep
            if threading._sleep != sleep:
                threading._sleep = sleep

def instrument_gevent_monkey(module):
    wrap_post_function(module, 'patch_thread', _patch_thread)
