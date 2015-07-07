import functools
import glob
import os
import pkgutil

_all_builtins = {}
_loaded_builtins = False

def builtin(fn):
    _all_builtins[fn.__name__] = fn
    return fn

def _load_builtins():
    for loader, name, _ in pkgutil.walk_packages(__path__, __name__ + '.'):
        loader.find_module(name).load_module(name)

def bind(build_inputs, env):
    global _loaded_builtins
    if not _loaded_builtins:
        _load_builtins()
        _loaded_builtins = True

    result = {}
    for k, v in _all_builtins.iteritems():
        result[k] = functools.partial(v, build_inputs, env)
    return result
