import fnmatch
import os
from collections import Iterable

from builtins import builtin

def listify(thing):
    if thing is None:
        return []
    elif isinstance(thing, Iterable) and not isinstance(thing, basestring):
        return thing
    else:
        return [thing]

def strlistify(thing):
    return (str(i) for i in listify(thing))

@builtin
def find(build_inputs, base='.', name='*', type=None):
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
