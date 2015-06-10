import os
import shell
from collections import Iterable

def isiterable(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, basestring)

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

def tween(iterable, delim, prefix=None, suffix=None, flag=True):
    def item(tween, value):
        return (tween, value) if flag else value

    first = True
    for i in iterable:
        if first:
            first = False
            if prefix is not None:
                yield item(True, prefix)
        else:
            yield item(True, delim)
        yield item(False, i)
    if not first and suffix is not None:
        yield item(True, suffix)

def flatten(iterable):
    for i in iterable:
        if isiterable(i):
            for j in i:
                yield j
        else:
            yield i

def first(thing):
    if isiterable(thing):
        return next(iter(thing))
    else:
        return thing

def uniques(iterable):
    def generate_uniques(iterable):
        seen = set()
        for item in iterable:
            if item not in seen:
                seen.add(item)
                yield item
    return list(generate_uniques(iterable))

def listify(thing, always_copy=False):
    if not always_copy and type(thing) == list:
        return thing
    return list(iterate(thing))

def shell_listify(thing):
    if thing is None:
        return []
    elif isiterable(thing):
        return list(thing)
    else:
        return shell.split(thing)

def objectify(x, valid_type, creator=None, **kwargs):
    if isinstance(x, valid_type):
        return x
    elif not isinstance(x, basestring):
        raise TypeError('expected a {} or a string'.format(valid_type))
    elif creator:
        return creator(x)
    else:
        return valid_type(x, **kwargs)
