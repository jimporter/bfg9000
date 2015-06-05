from collections import Iterable

def safe_str(s):
    if isinstance(s, basestring):
        return s
    elif hasattr(s, '_safe_str'):
        return s._safe_str()
    else:
        raise NotImplementedError()

class safe_string(object):
    pass

class escaped_str(safe_string):
    def __init__(self, string):
        if not isinstance(string, basestring):
            raise TypeError('expected a string')
        self.string = string

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '`{}`'.format(self.string)

    def _safe_str(self):
        return self

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
        self.bits = []
        for i in args:
            if isinstance(i, jbos):
                self.bits.extend(i.bits)
            elif isinstance(i, basestring) or isinstance(i, safe_string):
                self.bits.append(i)
            else:
                raise TypeError()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return 'jbos({})'.format(', '.join(repr(i) for i in self.bits))

    def _safe_str(self):
        return self

    def __add__(self, rhs):
        return jbos(self, rhs)

    def __radd__(self, lhs):
        return jbos(lhs, self)
