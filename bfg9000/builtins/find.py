import fnmatch
import os
import posixpath

from . import builtin
from ..iterutils import iterate
from ..backends.make.syntax import Writer, Syntax

depfile_name = '.bfg_find_deps'
def write_depfile(path, output, seen_dirs, makeify=False):
    with open(path, 'w') as f:
        out = Writer(f)
        out.write(output, Syntax.target)
        out.write_literal(':')
        for i in seen_dirs:
            out.write_literal(' ')
            out.write(os.path.abspath(i), Syntax.dependency)
        out.write_literal('\n')
        if makeify:
            for i in seen_dirs:
                out.write(os.path.abspath(i), Syntax.target)
                out.write_literal(':\n')

def _listdir(path):
    dirs, nondirs = [], []
    try:
        names = os.listdir(path)
        for name in names:
            if os.path.isdir(os.path.join(path, name)):
                dirs.append(name)
            else:
                nondirs.append(name)
    except:
        pass
    return dirs, nondirs

def _walk_flat(top):
    yield (top,) + _listdir(top)

def _walk_recursive(top):
    dirs, nondirs = _listdir(top)
    yield top, dirs, nondirs
    for name in dirs:
        path = posixpath.join(top, name)
        if not os.path.islink(path):
            for i in _walk_recursive(path):
                yield i

# FIXME: Always use forward slashes for path delimiters here? That way filtering
# the results after the fact is predictable.
def _find_files(paths, name, type, flat):
    results = []
    seen_dirs = []

    # "Does the walker choose the path, or the path the walker?" - Garth Nix
    walker = _walk_flat if flat else _walk_recursive

    def _filter_join(base, files, name):
        return (posixpath.join(base, i) for i in fnmatch.filter(files, name))

    for p in iterate(paths):
        if type != 'f' and fnmatch.fnmatch(p, name):
            results.append(p)

        generator = walker(p)
        for path, dirs, files in generator:
            seen_dirs.append(path)
            if type != 'f':
                results.extend(_filter_join(path, dirs, name))
            if type != 'd':
                results.extend(_filter_join(path, files, name))

    return results, seen_dirs

def find(path='.', name='*', type=None, flat=False):
    return _find_files(path, name, type, flat)[0]

@builtin
def find_files(build_inputs, env, path='.', name='*', type=None, flat=False,
               cache=True):
    results, seen_dirs = _find_files(path, name, type, flat)
    if cache:
        build_inputs.find_dirs.update(seen_dirs)
    return results
