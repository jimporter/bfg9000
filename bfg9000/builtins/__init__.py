import importlib
import os
import pkgutil
from functools import partial

_all_builtins = {}
_loaded_builtins = False

class Binder(object):
    def __init__(self, args, fn):
        self.__args = args
        self.__fn = fn

    def bind(self, *args, **kwargs):
        if args and kwargs:
            raise TypeError('positional and keyword arguments cannot be ' +
                            'passed together')
        if kwargs:
            return partial(self.__fn, *[kwargs[i] for i in self.__args])

        if len(args) != len(self.__args):
            raise ValueError('binder takes exactly {} arguments ({} given)'
                             .format( len(self.__args), len(args) ))
        return partial(self.__fn, *args)

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

    result = {}
    for k, v in _all_builtins.iteritems():
        result[k] = v.bind(**kwargs)

    # XXX: Make this more generic?
    result['env'] = kwargs['env']
    return result
