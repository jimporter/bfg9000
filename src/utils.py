import fnmatch
import os

from builtins import builtin

__all_searches__ = []

@builtin
def find(base='.', name='*', type=None):
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
    __all_searches__.append({
        'base': base, 'name': name, 'type': type, 'results': results
    })
    return results
