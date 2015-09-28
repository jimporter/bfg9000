import iterutils

class safe_string(object):
    pass

def safe_str(s):
    if isinstance(s, basestring) or isinstance(s, safe_string):
        return s
    elif hasattr(s, '_safe_str'):
        return s._safe_str()
    else:
        raise NotImplementedError(type(s))

class escaped_str(safe_string):
    def __init__(self, string):
        if not isinstance(string, basestring):
            raise TypeError('expected a string')
        self.string = string

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`{}`'.format(self.string)

    def __cmp__(self, rhs):
        if not isinstance(rhs, escaped_str):
            return NotImplemented
        return cmp(self.string, rhs.string)

    def __add__(self, rhs):
        return jbos(self, rhs)

    def __radd__(self, lhs):
        return jbos(lhs, self)

class jbos(safe_string): # Just a Bunch of Strings
    def __init__(self, *args):
        self.__bits = tuple(self.__flatten(args))

    @staticmethod
    def __flatten(value):
        for i in value:
            if isinstance(i, jbos):
                for j in i.bits:
                    yield j
            elif isinstance(i, basestring) or isinstance(i, safe_string):
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
        return jbos(self, rhs)

    def __radd__(self, lhs):
        return jbos(lhs, self)

def join(iterable, delim):
    return sum(iterutils.tween(iterable, delim), jbos())
