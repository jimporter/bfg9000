import fnmatch
import os

from . import builtin
from ..utils import listify

depfile_name = '.bfg_find_deps'
def write_depfile(path, output, seen_dirs, makeify=False):
    with open(path, 'w') as out:
        out.write(output + ':')
        for i in seen_dirs:
            out.write(' ' + os.path.abspath(i))
        out.write('\n')
        if makeify:
            for i in seen_dirs:
                out.write(os.path.abspath(i) + ':\n')

def _walk_flat(path):
    names = os.listdir(path)
    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(path, name)):
            dirs.append(name)
        else:
            nondirs.append(name)
    yield path, dirs, nondirs

def _find_files(paths, name, type, flat):
    results = []
    seen_dirs = []
    for p in paths:
        if type != 'f' and fnmatch.fnmatch(p, name):
            results.append(p)

        generator = _walk_flat(p) if flat else os.walk(p)
        for path, dirs, files in generator:
            seen_dirs.append(path)

            if type != 'f':
                results.extend(
                    os.path.join(path, i) for i in fnmatch.filter(dirs, name)
                )
            if type != 'd':
                results.extend(
                    os.path.join(path, i) for i in fnmatch.filter(files, name)
                )

    return results, seen_dirs

@builtin
def find_files(build_inputs, env, path='.', name='*', type=None, flat=False,
               cache=True):
    results, seen_dirs = _find_files(listify(path), name, type, flat)
    if cache:
        build_inputs.find_dirs.update(seen_dirs)
    return results
