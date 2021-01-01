from collections.abc import Iterable, Mapping, Sequence
from functools import reduce

__all__ = ['default_sentinel', 'first', 'find_index', 'flatten', 'isiterable',
           'ismapping', 'iterate', 'iterate_each', 'listify', 'list_view',
           'map_iterable', 'merge_dicts', 'merge_into_dict', 'partition',
           'recursive_walk', 'slice_dict', 'tween', 'uniques', 'unlistify']


# This could go in a funcutils module if we ever create one...
class _DefaultType:
    def __bool__(self):
        return False

    def __repr__(self):
        return '<default_sentinel>'


default_sentinel = _DefaultType()


def isiterable(thing):
    return (isinstance(thing, Iterable) and not isinstance(thing, str) and
            not ismapping(thing))


def ismapping(thing):
    return isinstance(thing, Mapping)


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


def iterate_each(things):
    for i in things:
        for j in iterate(i):
            yield j


def map_iterable(func, thing):
    if thing is None:
        return None
    elif isiterable(thing):
        t = type(thing) if isinstance(thing, (list, tuple)) else list
        return t(func(i) for i in thing)
    else:
        return func(thing)


def partition(func, iterable):
    return reduce(lambda result, i: result[not func(i)].append(i) or result,
                  iterable, ([], []))


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


def find_index(fn, seq):
    for i, elem in enumerate(seq):
        if fn(elem):
            return i
    return None


class list_view(Sequence):
    def __init__(self, container, start=None, stop=None):
        length = len(container)

        def clamp(n):
            return max(0, min(n, length))

        start = 0 if start is None else clamp(start)
        stop = length if stop is None else clamp(stop)

        if isinstance(container, list_view):
            self.data = container.data
            self.start = container.start + start
            self.stop = container.start + stop
        else:
            self.data = container
            self.start = start
            self.stop = stop

    def __getitem__(self, i):
        if isinstance(i, slice):
            if i.step != 1 and i.step is not None:
                raise ValueError(i)
            return list_view(self, i.start, i.stop)

        if i < 0 or i >= len(self):
            raise IndexError(i)
        return self.data[self.start + i]

    def __len__(self):
        return self.stop - self.start

    def split_at(self, i):
        return list_view(self, 0, i), list_view(self, i)


def merge_into_dict(dst, *args):
    for d in args:
        for k, v in d.items():
            curr = dst.get(k)
            if ismapping(v):
                if curr is None:
                    dst[k] = dict(v)
                elif ismapping(curr):
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
                if curr is not None and isiterable(curr) or ismapping(curr):
                    raise TypeError('type mismatch for {}'.format(k))
                dst[k] = v
            elif k not in dst:
                dst[k] = None  # v is always None here


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
