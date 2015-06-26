import fnmatch
import os
import json

from .builtins import builtin
from .utils import listify

class FindCache(object):
    version = 1
    cachefile = '.bfg_watch'

    def __init__(self):
        self._cache = []

    def add(self, args, results):
        self._cache.append((args, results))

    def __iter__(self):
        return iter(self._cache)

    def save(self, path):
        with open(path, 'w') as out:
            json.dump({
                'version': self.version,
                'cache': self._cache
            }, out)

    @classmethod
    def dirty(cls, path):
        try:
            with open(path) as inp:
                data = json.load(inp)
            if data['version'] > cls.version:
                # XXX: Issue a warning about downgrading?
                return True

            for args, old_results in data['cache']:
                if _find_files(*args) != old_results:
                    return True
            return False
        except:
            return True

def _walk_flat(path):
    names = os.listdir(path)
    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(path, name)):
            dirs.append(name)
        else:
            nondirs.append(name)
    yield path, dirs, nondirs

def _find_files(base, paths, name, type, flat):
    results = []
    for p in paths:
        if type != 'f' and fnmatch.fnmatch(p, name):
            results.append(p)
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
def find_files(build_inputs, env, path='.', name='*', type=None, flat=False,
               cache=True):
    args = (os.getcwd(), listify(path), name, type, flat)
    results = _find_files(*args)
    if cache:
        build_inputs.find_results.add(args, list(results))
    return results
