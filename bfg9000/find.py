import fnmatch
import os
import pickle

from .builtins import builtin
from .utils import listify

cachefile = '.bfg_watch'

class FindCache(object):
    def __init__(self):
        self._cache = []

    def add(self, args, results):
        self._cache.append((args, results))

    def __iter__(self):
        return iter(self._cache)

    def has_changes(self):
        for args, old_results in self:
            if _find(*args) != old_results:
                return True
        return False

    def save(self, path):
        with open(path, 'w') as out:
            pickle.dump(self, out, protocol=2)

    @staticmethod
    def load(path):
        with open(path) as inp:
            return pickle.load(inp)

def _walk_flat(path):
    names = os.listdir(path)
    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(path, name)):
            dirs.append(name)
        else:
            nondirs.append(name)
    yield path, dirs, nondirs

def _find(base, paths, name, type, flat):
    results = []
    for p in paths:
        full_path = os.path.join(base, p)
        generator = _walk_flat(full_path) if flat else os.walk(full_path)
        for path, dirs, files in generator:
            path = os.path.relpath(path, base)
            if type != 'f':
                results.extend((
                    os.path.join(path, i) for i in fnmatch.filter(dirs, name)
                ))
            if type != 'd':
                results.extend((
                    os.path.join(path, i) for i in fnmatch.filter(files, name)
                ))
    return results

@builtin
def find(build_inputs, env, path='.', name='*', type=None, flat=False):
    args = (os.getcwd(), listify(path), name, type, flat)
    results = _find(*args)
    build_inputs.find_results.add(args, list(results))
    return results
