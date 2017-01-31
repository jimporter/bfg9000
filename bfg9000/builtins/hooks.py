import functools
import inspect
import sys
from itertools import chain
from six import iteritems, itervalues, string_types

from ..iterutils import iterate

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
        def wrapper(*args, **kwargs):
            return self._fn(*(pre_args + args), **kwargs)

        if sys.version_info >= (3, 3):
            sig = inspect.signature(wrapper)
            params = list(sig.parameters.values())[len(kwargs):]
            wrapper.__signature__ = inspect.Signature(params)
        return wrapper


class _GetterBinder(_Binder):
    def __init__(self, fn, *args):
        _Binder.__init__(self, fn)
        self._args = args

    def bind(self, **kwargs):
        return self._fn(*[kwargs[i] for i in self._args])


class _PostWrapper(object):
    def __init__(self, fn, *args):
        self._fn = fn
        self._args = args

    def __call__(self, **kwargs):
        args = tuple(kwargs[i] for i in self._args)
        return self._fn(*args)


class _Decorator(object):
    def __init__(self, builtins, binder):
        self.__builtins = builtins
        self.__binder = binder

    def __call__(self, *args):
        def decorator(fn):
            self.__builtins[fn.__name__] = self.__binder(fn, *args)
            fn._builtin_bound = len(args)
            return fn
        return decorator


class Builtin(object):
    def __init__(self):
        self._builtins = {}
        self._decorator = _Decorator(self._builtins, _Binder)()
        self.globals = _Decorator(self._builtins, _PartialFunctionBinder)
        self.getter = _Decorator(self._builtins, _GetterBinder)

        self._post = {}
        self.post = _Decorator(self._post, _PostWrapper)

    def __call__(self, *args, **kwargs):
        return self._decorator(*args, **kwargs)

    @classmethod
    def type(cls, out_type, in_type=string_types):
        def decorator(fn):
            spec = inspect.getargspec(fn)

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                thing = cls._get_value(spec, wrapper._builtin_bound, args,
                                       kwargs)
                if isinstance(thing, wrapper.type):
                    return thing
                if not isinstance(thing, wrapper.in_type):
                    gen = (i.__name__ for i in chain(
                        [wrapper.type], iterate(wrapper.in_type))
                    )
                    raise TypeError('expected {}; but got {}'.format(
                        ', '.join(gen), type(thing).__name__
                    ))
                return fn(*args, **kwargs)

            wrapper.type = out_type
            wrapper.in_type = in_type
            return wrapper
        return decorator

    @staticmethod
    def _get_value(spec, builtin_bound, args, kwargs):
        if len(args) > builtin_bound:
            return args[builtin_bound]
        name = spec.args[builtin_bound]
        if name in kwargs:
            return kwargs[name]
        return spec.defaults[builtin_bound - len(spec.args)]

    def bind(self, **kwargs):
        builtins = {}
        for k, v in iteritems(self._builtins):
            builtins[k] = v.bind(builtins=builtins, **kwargs)

        builtins['__bfg9000__'] = builtins
        return builtins

    def run_post(self, builtins, **kwargs):
        for v in itervalues(self._post):
            v(builtins=builtins, **kwargs)


builtin = Builtin()
optbuiltin = Builtin()


@builtin.getter('env')
@optbuiltin.getter('env')
def env(_env):
    return _env
