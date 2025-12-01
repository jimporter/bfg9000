import enum
import sys
import typing
from collections import namedtuple
from inspect import Signature, Parameter

from . import safe_str
from .iterutils import isiterable
from .file_types import *
from .packages import Framework
from .path import BasePath


class option_list:
    def __init__(self, *args):
        self._options = []
        self.collect(*args)

    def append(self, option):
        if ( isinstance(option, safe_str.stringy_types) or
             not any(option.matches(i) for i in self._options) ):
            self._options.append(option)

    def extend(self, options):
        for i in options:
            self.append(i)

    def collect(self, *args):
        for i in args:
            if isiterable(i):
                for j in i:
                    self.collect(j)
            elif i is not None:
                self.append(i)

    def copy(self):
        return option_list(self._options)

    def filter(self, type):
        return option_list(i for i in self._options if isinstance(i, type))

    def __iter__(self):
        return iter(self._options)

    def __len__(self):
        return len(self._options)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return type(self)(self._options[key])
        return self._options[key]

    def __setitem__(self, key, value):
        self._options[key] = value

    def __eq__(self, rhs):
        return type(self) is type(rhs) and self._options == rhs._options

    def __ne__(self, rhs):
        return not (self == rhs)

    def __bool__(self):
        return bool(self._options)

    def __repr__(self):
        return '<option_list({})>'.format(repr(self._options))

    def __add__(self, rhs):
        x = self.copy()
        x += rhs
        return x

    def __iadd__(self, rhs):
        if not isinstance(rhs, option_list):
            raise TypeError('expected an option_list, got a {!r}'
                            .format(type(rhs)))
        self.extend(rhs)
        return self


class ForwardOptions:
    __slots__ = ['compile_options', 'link_options', 'libs', 'packages']

    def __init__(self, *, compile_options=None, link_options=None, libs=None,
                 packages=None):
        self.compile_options = compile_options or option_list()
        self.link_options = link_options or option_list()
        self.libs = libs or []
        self.packages = packages or []

    def update(self, rhs):
        for i in self.__slots__:
            getattr(self, i).extend(getattr(rhs, i))

    def __eq__(self, rhs):
        return all(getattr(self, i) == getattr(rhs, i) for i in self.__slots__)

    def __repr__(self):
        return repr({i: getattr(self, i) for i in self.__slots__})

    @classmethod
    def recurse(cls, libs):
        def do_recurse(result, libs):
            for i in libs:
                forward_opts = getattr(i, 'forward_opts', None)
                if forward_opts:
                    result.update(forward_opts)
                    do_recurse(result, forward_opts.libs)

        result = cls()
        do_recurse(result, libs)
        return result


variadic = namedtuple('variadic', ['type'])


def _get_ns_annotations(attrs):
    if '__annotations__' in attrs:
        return attrs['__annotations__']

    if sys.version_info >= (3, 14):
        import annotationlib
        annotate = annotationlib.get_annotate_from_class_namespace(attrs)
        if annotate:
            return annotationlib.call_annotate_function(
                annotate, format=annotationlib.Format.FORWARDREF
            )
    return {}


class OptionMeta(type):
    @staticmethod
    def __make_parameters(fields, defaults):
        has_variadic = False
        for k, v in fields.items():
            assert not has_variadic
            if isinstance(v, variadic):
                has_variadic = True
                kind = Parameter.VAR_POSITIONAL
                annotation = typing.Tuple[v.type]
            else:
                kind = Parameter.POSITIONAL_OR_KEYWORD
                annotation = v

            default = defaults.get(k, Parameter.empty)
            yield Parameter(k, kind, default=default, annotation=annotation)

    def __new__(cls, name, bases, attrs):
        annotations = _get_ns_annotations(attrs)
        slots = tuple(annotations.keys())
        defaults = {}
        for i in slots:
            if i in attrs:
                defaults[i] = attrs.pop(i)

        attrs.update({
            '__slots__': slots,
            '_signature': Signature(list(cls.__make_parameters(
                annotations, defaults
            )))
        })
        return type.__new__(cls, name, bases, attrs)


# This is like `typing.NamedTuple`, except with runtime type checking,
# promoting strings to enums, and allowing variadic values.
class Option(metaclass=OptionMeta):
    registry = {}

    @staticmethod
    def __check_type(typ, value):
        if not typ or isinstance(value, typ):
            return value
        elif isinstance(value, str) and issubclass(typ, enum.Enum):
            try:
                return typ[value]
            except Exception:
                raise ValueError('invalid {} {!r}'.format(typ.__name__, value))
        else:
            typ = [typ] if isinstance(typ, type) else typ
            raise TypeError('expected {}; but got {}'.format(
                ', '.join(i.__name__ for i in typ), type(value).__name__
            ))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.__name__] = cls

    def __init__(self, *args, **kwargs):
        bound = self._signature.bind(*args, **kwargs)
        bound.apply_defaults()

        for name, value in bound.arguments.items():
            param = self._signature.parameters[name]
            if param.kind == Parameter.VAR_POSITIONAL:
                annotation = typing.get_args(param.annotation)[0]
                value = [self.__check_type(annotation, i) for i in value]
            else:
                value = self.__check_type(param.annotation, value)
            setattr(self, name, value)

    @classmethod
    def alias(cls, fn):
        cls.registry[fn.__name__] = fn
        return fn

    def matches(self, rhs):
        return self == rhs

    def __eq__(self, rhs):
        return type(self) is type(rhs) and all(
            getattr(self, i) == getattr(rhs, i) for i in self.__slots__
        )

    def __ne__(self, rhs):
        return not (self == rhs)

    def __repr__(self):
        return '<{}({})>'.format(self.__class__.__name__, ', '.join(
            repr(getattr(self, i)) for i in self.__slots__
        ))


class OptionEnum(enum.Enum):
    def __repr__(self):
        return self.name


class OptionFlag(enum.Flag):
    def __repr__(self):
        return self.name


def option(name, /, **fields):
    return type(name, (Option,), {'__annotations__': fields})


def variadic_option(name, type=object):
    return option(name, value=variadic(type))


# Compilation options
include_dir = option('include_dir', directory=HeaderDirectory)
pch = option('pch', header=PrecompiledHeader)
pic = option('pic')
sanitize = option('sanitize')
std = option('std', value=str)

WarningValue = OptionEnum('WarningValue', ['disable', 'all', 'extra', 'error'])
warning = variadic_option('warning', WarningValue)


class define(Option):
    name: str
    value: (str, type(None)) = None


# Link options
entry_point = option('entry_point', value=str)
install_name_change = option('install_name_change', old=str, new=str)
lib = option('lib', library=(Library, Framework, str))
lib_dir = option('lib_dir', directory=Directory)
lib_literal = option('lib_literal', value=safe_str.stringy_types)
module_def = option('module_def', value=ModuleDefFile)
rpath_link_dir = option('rpath_link_dir', path=BasePath)


@Option.alias
def framework(name, suffix=None):
    return lib(Framework(name, suffix))


class gui(Option):
    main: bool = False


class RpathWhen(OptionFlag):
    installed = 1
    uninstalled = 2
    always = installed | uninstalled


class rpath_dir(Option):
    path: BasePath
    when: RpathWhen = RpathWhen.always


# General options
debug = option('debug')
lang = option('lang', value=str)
pthread = option('pthread')
static = option('static')

OptimizeValue = OptionEnum('OptimizeValue', ['disable', 'size', 'speed',
                                             'linktime'])
optimize = variadic_option('optimize', OptimizeValue)
