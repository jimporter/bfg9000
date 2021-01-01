import enum
from collections import namedtuple

from . import path, safe_str
from .iterutils import isiterable
from .file_types import *
from .packages import Framework


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
        return type(self) == type(rhs) and self._options == rhs._options

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


class OptionMeta(type):
    @staticmethod
    def _make_args(slots, types):
        has_variadic = False
        for s, t in zip(slots, types):
            assert not has_variadic
            if isinstance(t, variadic):
                has_variadic = True
                yield '*' + s
            else:
                yield s

    def __new__(cls, name, bases, attrs):
        fields = attrs.pop('_fields', [])
        slots = tuple(i[0] if isiterable(i) else i for i in fields)
        types = tuple(i[1] if isiterable(i) else None for i in fields)
        attrs.update({'__slots__': [i.replace('*', '') for i in slots],
                      '_types': types})

        if '__init__' not in attrs:
            exec('def __init__(self, {0}):\n    self._init({0})'.format(
                ', '.join(cls._make_args(slots, types))
            ), globals(), attrs)

        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        is_root = not any(type(i) == OptionMeta for i in bases)
        if is_root:
            cls.registry = {}
        else:
            cls.registry[name] = cls

        type.__init__(cls, name, bases, attrs)


class Option(metaclass=OptionMeta):
    def _init(self, *args):
        def check_type(v, t):
            if not t or isinstance(v, t):
                return v
            elif isinstance(v, str) and issubclass(t, enum.Enum):
                try:
                    return t[v]
                except Exception:
                    raise ValueError('invalid {} {!r}'.format(t.__name__, v))
            else:
                t = [t] if isinstance(t, type) else t
                raise TypeError('expected {}; but got {}'.format(
                    ', '.join(i.__name__ for i in t), type(v).__name__
                ))

        i = 0
        for k, t in zip(self.__slots__, self._types):
            if isinstance(t, variadic):
                v = [check_type(x, t.type) for x in args[i:]]
                i = len(args)
            else:
                v = check_type(args[i], t)
                i += 1
            setattr(self, k, v)

    def matches(self, rhs):
        return self == rhs

    def __eq__(self, rhs):
        return type(self) == type(rhs) and all(
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


def option(name, fields=[]):
    return type(name, (Option,), {'_fields': fields})


def variadic_option(name, type=None):
    return option(name, [('value', variadic(type))])


# Compilation options
include_dir = option('include_dir', [('directory', HeaderDirectory)])
pch = option('pch', [('header', PrecompiledHeader)])
pic = option('pic')
sanitize = option('sanitize')
std = option('std', [('value', str)])

WarningValue = OptionEnum('WarningValue', ['disable', 'all', 'extra', 'error'])
warning = variadic_option('warning', WarningValue)


class define(Option):
    _fields = [ ('name', str),
                ('value', (str, type(None))) ]

    def __init__(self, name, value=None):
        super()._init(name, value)


# Link options
entry_point = option('entry_point', [('value', str)])
install_name_change = option('install_name_change',
                             [('old', str), ('new', str)])
lib = option('lib', [('library', (Library, Framework, str))])
lib_dir = option('lib_dir', [('directory', Directory)])
lib_literal = option('lib_literal', [('value', safe_str.stringy_types)])
module_def = option('module_def', [('value', ModuleDefFile)])
rpath_link_dir = option('rpath_link_dir', [('path', path.BasePath)])


class gui(Option):
    _fields = [('main', bool)]

    def __init__(self, main=False):
        super()._init(main)


class RpathWhen(OptionFlag):
    installed = 1
    uninstalled = 2
    always = installed | uninstalled


class rpath_dir(Option):
    _fields = [ ('path', path.BasePath),
                ('when', RpathWhen) ]

    def __init__(self, path, when=RpathWhen.always):
        super()._init(path, when)


# General options
debug = option('debug')
lang = option('lang', [('value', str)])
pthread = option('pthread')
static = option('static')

OptimizeValue = OptionEnum('OptimizeValue', ['disable', 'size', 'speed',
                                             'linktime'])
optimize = variadic_option('optimize', OptimizeValue)
