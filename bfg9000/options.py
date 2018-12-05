import enum
from collections import namedtuple
from six import add_metaclass, string_types
from six.moves import zip

from . import path, safe_str
from .iterutils import isiterable, iterate
from .file_types import *
from .platforms.framework import Framework


class option_list(object):
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

    def __iter__(self):
        return iter(self._options)

    def __len__(self):
        return len(self._options)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self._options == rhs._options

    def __ne__(self, rhs):
        return not (self == rhs)

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


variadic = namedtuple('variadic', ['type'])


# XXX: This is a separate function to make Python 2.7.8 and earlier happy. For
# details, see <https://bugs.python.org/issue21591>.
def _make_init(slots, attrs):
    exec('def __init__(self, {0}):\n    self._init({0})'
         .format(', '.join(slots)), globals(), attrs)


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
            _make_init(cls._make_args(slots, types), attrs)

        return type.__new__(cls, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        is_root = not any(type(i) == OptionMeta for i in bases)
        if is_root:
            cls.registry = {}
        else:
            cls.registry[name] = cls

        type.__init__(cls, name, bases, attrs)


@add_metaclass(OptionMeta)
class Option(object):
    def _init(self, *args):
        def check_type(v, t):
            if not t or isinstance(v, t):
                return v
            elif isinstance(v, string_types) and issubclass(t, enum.Enum):
                try:
                    return t[v]
                except Exception:
                    raise ValueError('invalid {} {!r}'.format(t.__name__, v))
            else:
                raise TypeError('expected {}; but got {}'.format(
                    ', '.join(i.__name__ for i in iterate(t)), type(v).__name__
                ))

        i = 0
        for k, t in zip(self.__slots__, self._types):
            assert i < len(args)
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
        return repr(self.name)


def option(name, fields=[]):
    return type(name, (Option,), {'_fields': fields})


def variadic_option(name, type=None):
    return option(name, [('value', variadic(type))])


# Compilation options
include_dir = option('include_dir', [('directory', HeaderDirectory)])
std = option('std', [('value', str)])
pic = option('pic')
pch = option('pch', [('header', PrecompiledHeader)])
sanitize = option('sanitize')

WarningValue = OptionEnum('WarningValue', ['disable', 'all', 'extra', 'error'])
warning = variadic_option('warning', WarningValue)


class define(Option):
    _fields = [ ('name', str),
                ('value', (str, type(None))) ]

    def __init__(self, name, value=None):
        Option._init(self, name, value)


# Link options
lib_dir = option('lib_dir', [('directory', Directory)])
lib = option('lib', [('library', (Library, Framework, str))])
rpath_dir = option('rpath_dir', [('path', path.BasePath)])
rpath_link_dir = option('rpath_link_dir', [('path', path.BasePath)])
lib_literal = option('lib_literal', [('value', safe_str.stringy_types)])
module_def = option('module_def', [('value', ModuleDefFile)])
entry_point = option('entry_point', [('value', str)])

# General options
debug = option('debug')
pthread = option('pthread')

OptimizeValue = OptionEnum('OptimizeValue', ['disable', 'size', 'speed',
                                             'linktime'])
optimize = variadic_option('optimize', OptimizeValue)
