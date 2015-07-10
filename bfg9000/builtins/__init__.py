import functools
import importlib
import os
import pkgutil

_all_builtins = {}
_loaded_builtins = False

class Binder(object):
    def __init__(self, fn):
        self.fn = fn

    def bind(self, build_inputs, env):
        return functools.partial(self.fn, build_inputs, env)

def builtin(fn):
    bound = Binder(fn)
    _all_builtins[fn.__name__] = bound
    return bound

def _load_builtins():
    # XXX: There's probably a better way to do this.
    for _, name, _ in pkgutil.walk_packages(__path__, '.'):
        importlib.import_module(name, __package__)

def bind(build_inputs, env):
    global _loaded_builtins
    if not _loaded_builtins:
        _load_builtins()
        _loaded_builtins = True

    result = {}
    for k, v in _all_builtins.iteritems():
        result[k] = v.bind(build_inputs, env)
    result['env'] = env
    return result
