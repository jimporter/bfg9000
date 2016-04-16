import functools
import inspect
import sys
from six import iteritems

_all_builtins = {}


class _Binder(object):
    def __init__(self, args, fn):
        self._args = args
        self._fn = fn


class _FunctionBinder(_Binder):
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


class _VariableBinder(_Binder):
    def bind(self, **kwargs):
        return self._fn(*[kwargs[i] for i in self._args])


class _BuiltinDecorator(object):
    def __init__(self, binder):
        self.__binder = binder

    def __call__(self, *args):
        def wrapper(fn):
            bound = self.__binder(args, fn)
            _all_builtins[fn.__name__] = bound
            return bound
        return wrapper


builtin = _BuiltinDecorator(_FunctionBinder)()
builtin.globals = _BuiltinDecorator(_FunctionBinder)
builtin.variable = _BuiltinDecorator(_VariableBinder)


def bind(**kwargs):
    builtins = {}
    for k, v in iteritems(_all_builtins):
        builtins[k] = v.bind(builtins=builtins, **kwargs)

    return builtins


@builtin.variable('env')
def env(this_env):
    return this_env
