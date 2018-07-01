from six import string_types
from six.moves import zip

from . import iterutils


class safe_string(object):
    pass


stringy_types = string_types + (safe_string,)


def safe_str(s):
    if isinstance(s, stringy_types):
        return s
    elif hasattr(s, '_safe_str'):
        return s._safe_str()
    else:
        raise NotImplementedError(type(s))


class literal_types(safe_string):
    def __init__(self, string):
        if not isinstance(string, string_types):
            raise TypeError('expected a string')
        self.string = string

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`{}`'.format(self.string)

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return NotImplemented
        return self.string == rhs.string

    def __ne__(self, rhs):
        return not (self == rhs)

    def __add__(self, rhs):
        return jbos(self, rhs)

    def __radd__(self, lhs):
        return jbos(lhs, self)


class shell_literal(literal_types):
    """A string which has already been escaped for shell purposes, useful if
    you want to use characters with syntactic meaning in your shell (e.g. to
    use I/O redirection."""


class literal(literal_types):
    """A string which has already been escaped for *all* purposes (read: both
    shell and build files), useful if you want to use characters with syntactic
    meaning in your build script."""


class jbos(safe_string):  # Just a Bunch of Strings
    def __init__(self, *args):
        self.__bits = tuple(self.__flatten(args))

    @staticmethod
    def __flatten(value):
        for i in value:
            if isinstance(i, jbos):
                for j in i.bits:
                    yield j
            elif isinstance(i, (stringy_types)):
                yield i
            else:
                raise TypeError(type(i))

    @property
    def bits(self):
        return self.__bits

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return 'jbos({})'.format(', '.join(repr(i) for i in self.bits))

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return NotImplemented
        return ( len(self.bits) == len(rhs.bits) and
                 all(i == j for i, j in zip(self.bits, rhs.bits)) )

    def __ne__(self, rhs):
        return not (self == rhs)

    def __add__(self, rhs):
        if isinstance(rhs, stringy_types):
            return jbos(self, rhs)
        return NotImplemented

    def __radd__(self, lhs):
        if isinstance(lhs, stringy_types):
            return jbos(lhs, self)
        return NotImplemented


def join(iterable, delim):
    return sum(iterutils.tween(iterable, delim), jbos())
