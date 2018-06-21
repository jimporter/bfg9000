from . import iterutils, safe_str


class option_list(object):
    def __init__(self, *args, **kwargs):
        self._options = list(*args, **kwargs)

    def append(self, option):
        if ( isinstance(option, safe_str.stringy_types) or
             not any(option.matches(i) for i in self._options) ):
            self._options.append(option)

    def extend(self, options):
        for i in options:
            self.append(i)

    def copy(self):
        return option_list(self._options)

    def filter(self, type):
        return (i for i in self if isinstance(i, type))

    def __iter__(self):
        return iter(self._options)

    def __len__(self):
        return len(self._options)

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
        self._options.extend(rhs._options)
        return self


def flatten(iterables):
    return iterutils.flatten(iterables, option_list)


class pthread(object):
    def matches(self, rhs):
        return type(self) == type(rhs)
