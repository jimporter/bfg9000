import functools
import inspect
import sys
from six import iteritems

_all_builtins = {}


class _Binder(object):
    def __init__(self, fn):
        self._fn = fn

    def bind(self, **kwargs):
        return self._fn


class _PartialFunctionBinder(_Binder):
    def __init__(self, fn, *args):
        _Binder.__init__(self, fn)
        self._args = args

    def bind(self, **kwargs):
        pre_args = tuple(kwargs[i] for i in self._args)

        @functools.wraps(self._fn)
        def wrapped(*args, **kwargs):
            return self._fn(*(pre_args + args), **kwargs)

        if sys.version_info >= (3, 3):
            sig = inspect.signature(wrapped)
            params = list(sig.parameters.values())[len(kwargs):]
            wrapped.__signature__ = inspect.Signature(params)
        return wrapped


class _GetterBinder(_Binder):
    def __init__(self, fn, *args):
        _Binder.__init__(self, fn)
        self._args = args

    def bind(self, **kwargs):
        return self._fn(*[kwargs[i] for i in self._args])


class _BuiltinDecorator(object):
    def __init__(self, binder):
        self.__binder = binder

    def __call__(self, *args):
        def wrapper(fn):
            _all_builtins[fn.__name__] = self.__binder(fn, *args)
            return fn
        return wrapper


def _decorate_type(type):
    def wrapper(fn):
        fn.type = type
        return fn
    return wrapper


builtin = _BuiltinDecorator(_Binder)()
builtin.globals = _BuiltinDecorator(_PartialFunctionBinder)
builtin.getter = _BuiltinDecorator(_GetterBinder)
builtin.type = _decorate_type


def bind(**kwargs):
    builtins = {}
    for k, v in iteritems(_all_builtins):
        builtins[k] = v.bind(builtins=builtins, **kwargs)

    return builtins


@builtin.getter('env')
def env(this_env):
    return this_env
