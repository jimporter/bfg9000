import functools
from six import iteritems

_all_builtins = {}


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


def bind(**kwargs):
    builtins = {}
    for k, v in iteritems(_all_builtins):
        builtins[k] = v.bind(builtins=builtins, **kwargs)

    # XXX: Make this more generic?
    builtins['env'] = kwargs['env']
    return builtins
