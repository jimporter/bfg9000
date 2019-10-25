import functools
import inspect
import sys
from itertools import chain
from six import iteritems, iterkeys, itervalues, string_types

from ..iterutils import iterate, listify
from ..platforms.basepath import BasePath

string_or_path_types = string_types + (BasePath,)


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


def _get_argspec(fn):
    if sys.version_info >= (3, 3):
        return list(inspect.signature(fn).parameters.keys())
    return inspect.getargspec(fn).args


def _get_value(argspec, index, args, kwargs):
    # Get the value of the nth argument to this function, whether it's
    # passed positionally or as a keyword argument. Note that `index` should be
    # at least as large as the number of builtins bound to the function.
    if len(args) > index:
        return args[index]
    name = argspec[index]
    if name in kwargs:
        return kwargs[name]
    raise IndexError('unable to find user-provided argument')


def check_types(thing, expected_types, extra_types=[]):
    if not isinstance(thing, expected_types):
        types = chain(extra_types, expected_types)
        raise TypeError('expected {}; but got {}'.format(
            ', '.join(i.__name__ for i in types),
            __builtins__['type'](thing).__name__
        ))


def type(out_type, in_type=string_or_path_types, extra_in_type=(),
         short_circuit=True, first_optional=False):
    in_type = listify(in_type, type=tuple) + listify(extra_in_type, type=tuple)
    if first_optional:
        in_type = in_type + (__builtins__['type'](None),)

    def decorator(fn):
        spec = _get_argspec(fn)
        all_types = (out_type,) + in_type

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = getattr(wrapper, '_builtin_bound', 0)
            if first_optional and len(args) < 2 + bound:
                args = args[:bound] + (None, ) + args[bound:]

            # Try to get the first argument to this function. If it's the
            # output type, just return it immediately; otherwise, check if it's
            # a valid input type and then call the function.
            try:
                thing = _get_value(spec, bound, args, kwargs)
                if short_circuit:
                    if isinstance(thing, wrapper.type):
                        return thing
                    check_types(thing, wrapper.in_type, [wrapper.type])
                else:
                    check_types(thing, all_types)
            except IndexError:
                pass
            return fn(*args, **kwargs)

        wrapper.type = out_type
        wrapper.in_type = in_type
        return wrapper
    return decorator
