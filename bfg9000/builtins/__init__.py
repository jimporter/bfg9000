import functools
import importlib
import os
import pkgutil

_all_builtins = {}
_loaded_builtins = False

class Binder(object):
    def __init__(self, args, fn):
        self.__args = args
        self.__fn = fn

    def bind(self, **kwargs):
        # XXX: partial doesn't forward the docstring of the function.
        return functools.partial(self.__fn, *[kwargs[i] for i in self.__args])

def _decorate_builtin(*args):
    def wrapper(fn):
        bound = Binder(args, fn)
        _all_builtins[fn.__name__] = bound
        return bound
    return wrapper

builtin = _decorate_builtin()
builtin.globals = _decorate_builtin

def _load_builtins():
    # XXX: There's probably a better way to do this.
    for _, name, _ in pkgutil.walk_packages(__path__, '.'):
        importlib.import_module(name, __package__)

def bind(**kwargs):
    global _loaded_builtins
    if not _loaded_builtins:
        _load_builtins()
        _loaded_builtins = True

    builtins = {}
    for k, v in _all_builtins.iteritems():
        builtins[k] = v.bind(builtins=builtins, **kwargs)

    # XXX: Make this more generic?
    builtins['env'] = kwargs['env']
    return builtins
