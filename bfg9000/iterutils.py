from collections import Iterable
from itertools import chain
from six import iteritems, string_types

__all__ = ['first', 'isiterable', 'iterate', 'listify', 'merge_dicts',
           'merge_into_dict', 'objectify', 'tween', 'uniques', 'unlistify']


# XXX: This isn't exactly an iterator utility, but this file is close enough...
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
        # XXX: Come up with a way to provide args to prepend?
        return creator(thing, **kwargs)


def isiterable(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, string_types)


def iterate(thing):
    def generate_none():
        return
        yield

    def generate_one(x):
        yield x

    if thing is None:
        return generate_none()
    elif isiterable(thing):
        return iter(thing)
    else:
        return generate_one(thing)


def listify(thing, always_copy=False):
    if not always_copy and type(thing) == list:
        return thing
    return list(iterate(thing))


def first(thing):
    try:
        return next(iterate(thing))
    except StopIteration:
        raise LookupError()


def unlistify(thing):
    if len(thing) == 0:
        return None
    elif len(thing) == 1:
        return thing[0]
    else:
        return thing


def tween(iterable, delim, prefix=None, suffix=None):
    first = True
    for i in iterable:
        if first:
            first = False
            if prefix is not None:
                yield prefix
        else:
            yield delim
        yield i
    if not first and suffix is not None:
        yield suffix


def uniques(iterable):
    def generate_uniques(iterable):
        seen = set()
        for item in iterable:
            if item not in seen:
                seen.add(item)
                yield item
    return list(generate_uniques(iterable))


def merge_into_dict(dst, *args):
    for d in args:
        for k, v in iteritems(d):
            curr = dst.get(k)
            if isinstance(v, dict):
                if curr is None:
                    dst[k] = dict(v)
                elif isinstance(curr, dict):
                    merge_into_dict(curr, v)
                else:
                    raise TypeError('type mismatch for {}'.format(k))
            elif isiterable(v):
                if curr is None:
                    dst[k] = list(v)
                elif isiterable(curr):
                    curr.extend(v)
                elif not isiterable(curr):
                    raise TypeError('type mismatch for {}'.format(k))
            elif v is not None:
                if curr is not None and isiterable(curr):
                    raise TypeError('type mismatch for {}'.format(k))
                dst[k] = v


def merge_dicts(*args):
    dst = {}
    merge_into_dict(dst, *args)
    return dst
