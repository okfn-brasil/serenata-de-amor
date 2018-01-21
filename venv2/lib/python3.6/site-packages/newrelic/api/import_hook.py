import imp
import logging
import sys

_logger = logging.getLogger(__name__)

try:
    from importlib import find_loader
except ImportError:
    find_loader = None

_import_hooks = {}

# These modules are imported by the newrelic package and/or do not do nested
# imports, so they're ok to import before newrelic.
_ok_modules = ['urllib', 'urllib2', 'httplib', 'http.client', 'urllib.request',
        'newrelic.agent']


def register_import_hook(name, callable):
    imp.acquire_lock()

    try:
        hooks = _import_hooks.get(name, None)

        if name not in _import_hooks or hooks is None:

            # If no entry in registry or entry already flagged with
            # None then module may have been loaded, in which case
            # need to check and fire hook immediately.

            hooks = _import_hooks.get(name)

            module = sys.modules.get(name, None)

            if module is not None:

                # The module has already been loaded so fire hook
                # immediately.

                if module.__name__ not in _ok_modules:
                    _logger.debug('Module %s has been imported before the '
                            'newrelic.agent.initialize call. Import and '
                            'initialize the New Relic agent before all '
                            'other modules for best monitoring '
                            'results.' % module)

                _import_hooks[name] = None

                callable(module)

            else:

                # No hook has been registered so far so create list
                # and add current hook.

                _import_hooks[name] = [callable]

        else:

            # Hook has already been registered, so append current
            # hook.

            _import_hooks[name].append(callable)

    finally:
        imp.release_lock()


def _notify_import_hooks(name, module):

    # Is assumed that this function is called with the global
    # import lock held. This should be the case as should only
    # be called from load_module() of the import hook loader.

    hooks = _import_hooks.get(name, None)

    if hooks is not None:
        _import_hooks[name] = None

        for callable in hooks:
            callable(module)


class _ImportHookLoader:

    def load_module(self, fullname):

        # Call the import hooks on the module being handled.

        module = sys.modules[fullname]
        _notify_import_hooks(fullname, module)

        return module


class _ImportHookChainedLoader:

    def __init__(self, loader):
        self.loader = loader

    def load_module(self, fullname):
        module = self.loader.load_module(fullname)

        # Call the import hooks on the module being handled.

        _notify_import_hooks(fullname, module)

        return module


class ImportHookFinder:

    def __init__(self):
        self._skip = {}

    def find_module(self, fullname, path=None):

        # If not something we are interested in we can return.

        if fullname not in _import_hooks:
            return None

        # Check whether this is being called on the second time
        # through and return.

        if fullname in self._skip:
            return None

        # We are now going to call back into import. We set a
        # flag to see we are handling the module so that check
        # above drops out on subsequent pass and we don't go
        # into an infinite loop.

        self._skip[fullname] = True

        try:
            # For Python 3 we need to use find_loader() from the new
            # importlib module.

            if find_loader:
                loader = find_loader(fullname, path)

                if loader:
                    return _ImportHookChainedLoader(loader)

            else:
                __import__(fullname)

                # If we get this far then the module we are
                # interested in does actually exist and so return
                # our loader to trigger import hooks and then return
                # the module.

                return _ImportHookLoader()

        finally:
            del self._skip[fullname]


def import_hook(name):
    def decorator(wrapped):
        register_import_hook(name, wrapped)
        return wrapped
    return decorator


def import_module(name):
    __import__(name)
    return sys.modules[name]
