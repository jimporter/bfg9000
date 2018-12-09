from collections import Iterable
from six import iteritems, string_types

__all__ = ['default_sentinel', 'first', 'flatten', 'isiterable', 'iterate',
           'listify', 'merge_dicts', 'merge_into_dict', 'recursive_walk',
           'slice_dict', 'tween', 'uniques', 'unlistify']

# This could go in a funcutils module if we ever create one...
default_sentinel = object()


def isiterable(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, string_types)


def iterate(thing):
    def generate_none():
        return iter(())

    def generate_one(x):
        yield x

    if thing is None:
        return generate_none()
    elif isiterable(thing):
        return iter(thing)
    else:
        return generate_one(thing)


def listify(thing, always_copy=False, scalar_ok=True, type=list):
    if not always_copy and isinstance(thing, type):
        return thing
    if scalar_ok:
        thing = iterate(thing)
    elif not isiterable(thing):
        raise TypeError('expected an iterable')
    return type(thing)


def first(thing, default=default_sentinel):
    try:
        return next(iterate(thing))
    except StopIteration:
        if default is not default_sentinel:
            return default
        raise LookupError()


def unlistify(thing):
    if len(thing) == 0:
        return None
    elif len(thing) == 1:
        return thing[0]
    else:
        return thing


def flatten(iterables, type=list):
    result = type()
    # Performance tests on the kinds of data common in bfg (generators calling
    # a function returning a list on each step) show that this is consistently
    # faster than using `list(chain.from_iterable(iterables))`. It's also
    # *much* faster than using `sum(iterables, [])`.
    for i in iterables:
        result.extend(i)
    return result


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


def recursive_walk(thing, attr, children_attr=None):
    for i in getattr(thing, attr):
        yield i
    for i in getattr(thing, children_attr or attr):
        for j in recursive_walk(i, attr, children_attr):
            yield j


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
                    dst[k] = type(v)(v)
                elif isiterable(curr):
                    curr.extend(v)
                else:
                    raise TypeError('type mismatch for {}'.format(k))
            elif v is not None:
                if curr is not None and isiterable(curr):
                    raise TypeError('type mismatch for {}'.format(k))
                dst[k] = v


def merge_dicts(*args):
    dst = {}
    merge_into_dict(dst, *args)
    return dst


def slice_dict(d, keys):
    result = {}
    for k in keys:
        if k in d:
            result[k] = d.pop(k)
    return result
