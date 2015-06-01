import fnmatch
import os
import shlex
from collections import Iterable

from builtins import builtin

def _generate_none():
    return
    yield

def _generate_one(x):
    yield x

def iterate(thing):
    if thing is None:
        return _generate_none()
    elif isinstance(thing, Iterable) and not isinstance(thing, basestring):
        return iter(thing)
    else:
        return _generate_one(thing)

def tween(iterable, delim, prefix=None, suffix=None):
    first = True
    for i in iterable:
        if first:
            first = False
            if prefix is not None:
                yield True, prefix
        else:
            yield True, delim
        yield False, i
    if not first and suffix is not None:
        yield True, suffix

def flatten(iterable):
    for i in iterable:
        if isinstance(i, Iterable) and not isinstance(i, basestring):
            for j in i:
                yield j
        else:
            yield i

def listify(thing):
    return list(iterate(thing))

def shell_listify(thing):
    if thing is None:
        return []
    elif isinstance(thing, Iterable) and not isinstance(thing, basestring):
        return list(thing)
    else:
        return shlex.split(thing, posix=False)

def objectify(x, valid_type, creator=None, **kwargs):
    if isinstance(x, valid_type):
        return x
    elif not isinstance(x, basestring):
        raise TypeError('expected a {} or a string'.format(valid_type))
    elif creator:
        return creator(x)
    else:
        return valid_type(x, **kwargs)

@builtin
def find(build_inputs, env, base='.', name='*', type=None):
    results = []
    for path, dirs, files in os.walk(base):
        if type != 'f':
            results.extend((
                os.path.join(path, i) for i in fnmatch.filter(dirs, name)
            ))
        if type != 'd':
            results.extend((
                os.path.join(path, i) for i in fnmatch.filter(files, name)
            ))
    return results
