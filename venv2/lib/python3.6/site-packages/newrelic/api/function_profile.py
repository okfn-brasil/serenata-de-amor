import cProfile
import functools
import os
import threading
import time

from newrelic.common.object_wrapper import FunctionWrapper, wrap_object

class FunctionProfile(object):

    def __init__(self, profile):
        self.profile = profile

    def __enter__(self):
        self.profile.enable()
        return self

    def __exit__(self, exc, value, tb):
        self.profile.disable()
        pass

class FunctionProfileSession(object):

    def __init__(self, filename, delay=1.0, checkpoint=30):
        self.filename = filename % { 'pid': os.getpid() }
        self.delay = delay
        self.checkpoint = checkpoint

        self.lock = threading.Lock()
        self.profile = cProfile.Profile()

        self.last = time.time() - delay

        self.active = False
        self.count = 0

    def __call__(self, wrapped, instance, args, kwargs):
        with self.lock:
            if self.active:
                return wrapped(*args, **kwargs)

            if time.time() - self.last < self.delay:
                return wrapped(*args, **kwargs)

            self.active = True
            self.count += 1

        try:
            with FunctionProfile(self.profile):
                result = wrapped(*args, **kwargs)

            if (self.count % self.checkpoint) == 0:
                self.profile.dump_stats(self.filename)

            return result

        finally:
            self.last = time.time()
            self.active = False

def FunctionProfileWrapper(wrapped, filename, delay=1.0, checkpoint=30):
    wrapper = FunctionProfileSession(filename, delay, checkpoint)
    return FunctionWrapper(wrapped, wrapper)

def function_profile(filename, delay=1.0, checkpoint=30):
    return functools.partial(FunctionProfileWrapper, filename=filename,
            delay=delay, checkpoint=checkpoint)

def wrap_function_profile(module, object_path, filename, delay=1.0,
        checkpoint=30):
    wrap_object(module, object_path, FunctionProfileWrapper,
            (filename, delay, checkpoint))
