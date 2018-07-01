import functools
from itertools import chain
from six import iteritems, string_types

from .iterutils import isiterable, iterate

__all__ = ['objectify', 'hashify', 'memoize']


def objectify(thing, valid_type, creator=None, in_type=string_types,
              **kwargs):
    if creator is None:
        creator = valid_type

    if isinstance(thing, valid_type):
        return thing
    elif not isinstance(thing, in_type):
        gen = (i.__name__ for i in chain([valid_type], iterate(in_type)))
        raise TypeError('expected {}; but got {}'.format(
            ', '.join(gen), type(thing).__name__
        ))
    else:
        return creator(thing, **kwargs)


def hashify(thing):
    if isinstance(thing, dict):
        return frozenset((hashify(k), hashify(v)) for k, v in iteritems(thing))
    elif isiterable(thing):
        return tuple(hashify(i) for i in thing)
    return thing


def memoize(fn):
    cache = {}

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (hashify(args), hashify(kwargs))
        if key in cache:
            return cache[key]
        result = cache[key] = fn(*args, **kwargs)
        return result

    def reset():
        cache.clear()

    wrapper._reset = reset
    return wrapper
