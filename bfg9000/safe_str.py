import string as _string
from six.moves import filter as ifilter
from six import string_types
from six.moves import zip

from . import iterutils


class safe_string(object):
    def _safe_format(self, format_spec):
        return self

    def __add__(self, rhs):
        return jbos(self, safe_str(rhs))

    def __radd__(self, lhs):
        return jbos(safe_str(lhs), self)


class safe_string_ops(object):
    def __add__(self, rhs):
        return jbos(safe_str(self), safe_str(rhs))

    def __radd__(self, lhs):
        return jbos(safe_str(lhs), safe_str(self))


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
        self.__bits = tuple(self.__canonicalize(args))

    @staticmethod
    def __canonicalize(value):
        def flatten_bits(value):
            for i in value:
                if isinstance(i, jbos):
                    for j in i.bits:
                        yield j
                elif isinstance(i, stringy_types):
                    yield i
                else:
                    raise TypeError(type(i))

        bits = ifilter(None, flatten_bits(value))
        try:
            last = next(bits)
        except StopIteration:
            return

        for i in bits:
            same_type = type(i) == type(last)
            if same_type and isinstance(i, string_types):
                last += i
            elif same_type and isinstance(i, literal_types):
                last = type(i)(last.string + i.string)
            else:
                yield last
                last = i
        yield last

    @property
    def bits(self):
        return self.__bits

    def simplify(self):
        if len(self.bits) == 0:
            return ''
        elif len(self.bits) == 1:
            return self.bits[0]
        return self

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '|{}|'.format(', '.join(repr(i) for i in self.bits))

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return NotImplemented
        return ( len(self.bits) == len(rhs.bits) and
                 all(i == j for i, j in zip(self.bits, rhs.bits)) )

    def __ne__(self, rhs):
        return not (self == rhs)


def join(iterable, delim):
    if delim:
        iterable = iterutils.tween(iterable, delim)
    return sum(iterable, jbos()).simplify()


def format_field(value, format_spec):
    t = type(value)
    if hasattr(t, '_safe_format'):
        return t._safe_format(value, format_spec)
    elif hasattr(value, '_safe_str'):
        return format_field(value._safe_str(), format_spec)
    return __builtins__['format'](value, format_spec)


class Formatter(_string.Formatter):
    def format_field(self, value, format_spec):
        return format_field(value, format_spec)

    # We need to copy these from the Python stdlib implementation to change the
    # join() call at the end of _vformat (and to get automatic field numbering
    # in Python 2.7...)
    def vformat(self, format_string, args, kwargs):
        used_args = set()
        result, _ = self._vformat(format_string, args, kwargs, used_args, 2)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth,
                 auto_arg_index=0):
        if recursion_depth < 0:  # pragma: no cover
            raise ValueError('Max string recursion exceeded')
        result = []
        for literal_text, field_name, format_spec, conversion in \
                self.parse(format_string):

            # output the literal text
            if literal_text:
                result.append(literal_text)

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # handle arg indexing when empty field_names are given.
                if field_name == '':
                    if auto_arg_index is False:
                        raise ValueError('cannot switch from manual field '
                                         'specification to automatic field '
                                         'numbering')
                    field_name = str(auto_arg_index)
                    auto_arg_index += 1
                elif field_name.isdigit():
                    if auto_arg_index:
                        raise ValueError('cannot switch from manual field '
                                         'specification to automatic field '
                                         'numbering')
                    # disable auto arg incrementing, if it gets
                    # used later on, then an exception will be raised
                    auto_arg_index = False

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, if needed
                format_spec, auto_arg_index = self._vformat(
                    format_spec, args, kwargs,
                    used_args, recursion_depth - 1,
                    auto_arg_index=auto_arg_index)

                # format the object and append to the result
                result.append(self.format_field(obj, format_spec))

        return join(result, ''), auto_arg_index


_fmt = Formatter()


def safe_format(*args, **kwargs):
    return _fmt.format(*args, **kwargs)
