import functools
import inspect
from contextlib import contextmanager
from itertools import chain

from ..iterutils import iterate, listify
from ..platforms.basepath import BasePath

string_or_path_types = (str, BasePath)


class Builtins:
    def __init__(self):
        self._default = {}
        self._post = {}

    def add(self, kind, name, value):
        assert kind in ('default', 'post')
        getattr(self, '_' + kind)[name] = value

    def bind(self, context):
        builtins = {}
        for k, v in self._default.items():
            builtins[k] = v.bind(context=context)

        builtins['__bfg9000__'] = builtins
        return builtins

    def run_post(self, context):
        for v in self._post.values():
            v(context=context)


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
        context = _allbuiltins.keys()
    for i in iterate(context):
        _allbuiltins[i].add(kind, name, value)


class BaseContext:
    def __init__(self, env):
        self.env = env
        self.builtins = _allbuiltins[self.kind].bind(context=self)

    def __getitem__(self, key):
        return self.builtins[key]

    def run_post(self):
        _allbuiltins[self.kind].run_post(context=self)


class StackContext(BaseContext):
    class PathEntry:
        def __init__(self, path):
            self.path = path
            self.exports = {}

    def __init__(self, env):
        self.seen_paths = []
        self.path_stack = []
        super().__init__(env)

    @contextmanager
    def push_path(self, path):
        self.seen_paths.append(path)
        self.path_stack.append(self.PathEntry(path))
        try:
            yield self.path_stack[-1]
        finally:
            self.path_stack.pop()

    @property
    def path(self):
        return self.path_stack[-1].path

    @property
    def exports(self):
        if len(self.path_stack) == 1:
            raise ValueError('exports are not allowed on root-level bfg ' +
                             'scripts')
        return self.path_stack[-1].exports


class BuildContext(StackContext):
    kind = 'build'
    filename = 'build.bfg'

    def __init__(self, env, build, argv):
        self.build = build
        self.argv = argv
        super().__init__(env)


class OptionsContext(StackContext):
    kind = 'options'
    filename = 'options.bfg'

    def __init__(self, env, parser):
        self.parser = parser
        super().__init__(env)


class ToolchainContext(BaseContext):
    kind = 'toolchain'

    def __init__(self, env, reload):
        self.reload = reload
        self._pushed_path = False
        super().__init__(env)

    @contextmanager
    def push_path(self, path):
        # Toolchains don't allow submodules, so we can only call push_path
        # once.
        assert not self._pushed_path
        self._pushed_path = True
        yield


class _Binder:
    builtin_bound = 0

    def __init__(self, fn):
        self._fn = fn

    def bind(self, context):
        return self._fn


class _PartialFunctionBinder(_Binder):
    builtin_bound = 1

    def bind(self, context):
        @functools.wraps(self._fn)
        def wrapper(*args, **kwargs):
            return self._fn(context, *args, **kwargs)

        sig = inspect.signature(wrapper)
        params = list(sig.parameters.values())[self.builtin_bound:]
        wrapper.__signature__ = inspect.Signature(params)
        return wrapper


class _GetterBinder(_Binder):
    builtin_bound = 1

    def bind(self, context):
        return self._fn(context)


class _Decorator:
    def __init__(self, binder):
        self.__binder = binder

    def __call__(self, context='build', name=None):
        def decorator(fn):
            _add_builtin(context, 'default', name or fn.__name__,
                         self.__binder(fn))
            fn._builtin_bound = self.__binder.builtin_bound
            return fn
        return decorator


default = _Decorator(_Binder)
function = _Decorator(_PartialFunctionBinder)
getter = _Decorator(_GetterBinder)


def post(context='build', name=None):
    def decorator(fn):
        _add_builtin(context, 'post', name or fn.__name__, fn)
        return fn
    return decorator


def _get_argspec(fn):
    return list(inspect.signature(fn).parameters.keys())


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
