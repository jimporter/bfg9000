from six import add_metaclass
from six.moves import zip

from . import path, safe_str
from .iterutils import isiterable, iterate
from .file_types import *
from .frameworks import Framework


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


# XXX: This is a separate function to make Python 2.7.8 and earlier happy. For
# details, see <https://bugs.python.org/issue21591>.
def _make_init(slots, attrs):
    exec('def __init__(self, {0}):\n    self._init({0})'
         .format(', '.join(slots)), globals(), attrs)


class OptionMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = attrs.pop('_fields', [])
        slots = tuple(i[0] if isiterable(i) else i for i in fields)
        types = tuple(i[1] if isiterable(i) else None for i in fields)
        attrs.update({'__slots__': slots, '_types': types})

        if '__init__' not in attrs:
            _make_init(slots, attrs)

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
        assert len(args) == len(self.__slots__)
        for k, t, v in zip(self.__slots__, self._types, args):
            if t and not isinstance(v, t):
                raise TypeError('expected {}; but got {}'.format(
                    ', '.join(i.__name__ for i in iterate(t)), type(v).__name__
                ))
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


def option(name, fields=()):
    return type(name, (Option,), {'_fields': fields})


# Compilation options
include_dir = option('include_dir', [('directory', HeaderDirectory)])
std = option('std', [('value', str)])
pic = option('pic')
pch = option('pch', [('header', PrecompiledHeader)])


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
entry_point = option('entry_point', [('value', str)])

# General options
pthread = option('pthread')
