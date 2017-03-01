from six import string_types

from . import iterutils


class safe_string(object):
    pass


def safe_str(s):
    if isinstance(s, (string_types, safe_string)):
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
            elif isinstance(i, (string_types, safe_string)):
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

    def __add__(self, rhs):
        if isinstance(rhs, (jbos, string_types, safe_string)):
            return jbos(self, rhs)
        return NotImplemented

    def __radd__(self, lhs):
        if isinstance(lhs, (jbos, string_types, safe_string)):
            return jbos(lhs, self)
        return NotImplemented


def join(iterable, delim):
    return sum(iterutils.tween(iterable, delim), jbos())
