import functools
import inspect
import sys
from itertools import chain
from six import iteritems, iterkeys, itervalues, string_types

from ..iterutils import iterate


class Builtins(object):
    def __init__(self):
        self._default = {}
        self._post = {}

    def add(self, kind, name, value):
        assert kind in ('default', 'post')
        getattr(self, '_' + kind)[name] = value

    def bind(self, **kwargs):
        builtins = {}
        for k, v in iteritems(self._default):
            builtins[k] = v.bind(builtins=builtins, **kwargs)

        builtins['__bfg9000__'] = builtins
        return builtins

    def run_post(self, builtins, **kwargs):
        for v in itervalues(self._post):
            v(builtins=builtins, **kwargs)


build = Builtins()
options = Builtins()
toolchain = Builtins()
_allbuiltins = {
    'build': build,
    'options': options,
    'toolchain': toolchain,
}


def _add_builtin(context, kind, name, value):
    if context == '*':
        context = iterkeys(_allbuiltins)
    for i in iterate(context):
        _allbuiltins[i].add(kind, name, value)


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
        if not self._args:
            return _Binder.bind(self, **kwargs)
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
    def __init__(self, kind, binder):
        self.__kind = kind
        self.__binder = binder

    def __call__(self, *args, **kwargs):
        context = kwargs.pop('context', 'build')
        name = kwargs.pop('name', None)

        def decorator(fn):
            _add_builtin(context, self.__kind, name or fn.__name__,
                         self.__binder(fn, *args))
            fn._builtin_bound = len(args)
            return fn
        return decorator


function = _Decorator('default', _PartialFunctionBinder)
getter = _Decorator('default', _GetterBinder)
post = _Decorator('post', _PostWrapper)


def _get_value(argspec, builtin_bound, args, kwargs):
    # Get the value of the first argument to this function, whether it's
    # passed positionally or as a keyword argument.
    if len(args) > builtin_bound:
        return args[builtin_bound]
    name = argspec[builtin_bound]
    if name in kwargs:
        return kwargs[name]
    raise IndexError('unable to find user-provided argument')


# We need to use the `type()` built-in inside our function that's *also* called
# `type`!
_type = type


def type(out_type, in_type=string_types):
    def decorator(fn):
        if sys.version_info >= (3, 3):
            argspec = list(inspect.signature(fn).parameters.keys())
        else:
            argspec = inspect.getargspec(fn).args

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Try to get the first argument to this function. If it's the
            # output type, just return it immediately; otherwise, check if
            # it's a valid input type and then call the function.
            try:
                thing = _get_value(argspec, wrapper._builtin_bound, args,
                                   kwargs)
                if isinstance(thing, wrapper.type):
                    return thing
                if not isinstance(thing, wrapper.in_type):
                    gen = (i.__name__ for i in chain(
                        [wrapper.type], iterate(wrapper.in_type))
                    )
                    raise TypeError('expected {}; but got {}'.format(
                        ', '.join(gen), _type(thing).__name__
                    ))
            except IndexError:
                pass
            return fn(*args, **kwargs)

        wrapper.type = out_type
        wrapper.in_type = in_type
        return wrapper
    return decorator
