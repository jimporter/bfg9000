import os
import shell
from collections import Iterable

def _generate_none():
    return
    yield

def _generate_one(x):
    yield x

def isiterable(thing):
    return isinstance(thing, Iterable) and not isinstance(thing, basestring)

def iterate(thing):
    if thing is None:
        return _generate_none()
    elif isiterable(thing):
        return iter(thing)
    else:
        return _generate_one(thing)

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
