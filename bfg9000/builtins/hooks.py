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


class _Decorator(object):
    def __init__(self, builtins, binder):
        self.__builtins = builtins
        self.__binder = binder

    def __call__(self, *args):
        def wrapper(fn):
            self.__builtins[fn.__name__] = self.__binder(fn, *args)
            return fn
        return wrapper


def _decorate_type(type):
    def wrapper(fn):
        fn.type = type
        return fn
    return wrapper


class Builtin(object):
    def __init__(self):
        self._builtins = {}
        self._decorator = _Decorator(self._builtins, _Binder)()
        self.globals = _Decorator(self._builtins, _PartialFunctionBinder)
        self.getter = _Decorator(self._builtins, _GetterBinder)

    def __call__(self, *args, **kwargs):
        return self._decorator(*args, **kwargs)

    @staticmethod
    def type(type):
        def wrapper(fn):
            fn.type = type
            return fn
        return wrapper

    def bind(self, **kwargs):
        builtins = {}
        for k, v in iteritems(self._builtins):
            builtins[k] = v.bind(builtins=builtins, **kwargs)

        builtins['__bfg9000__'] = builtins
        return builtins


builtin = Builtin()
optbuiltin = Builtin()


@builtin.getter('env')
@optbuiltin.getter('env')
def env(_env):
    return _env
