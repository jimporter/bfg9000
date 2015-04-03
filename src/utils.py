import fnmatch
import os

from builtins import builtin

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
