import fnmatch
import os
import posixpath
import re

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

def _find_files(paths, name, type, flat, filter):
    results = []
    seen_dirs = []

    # "Does the walker choose the path, or the path the walker?" - Garth Nix
    walker = _walk_flat if flat else _walk_recursive

    def _filter_in_place(files, type, func):
        for i in reversed(range( len(files) )):
            if not func(files[i], type):
                files.pop(i)

    def _filter_join(base, files, name):
        return (posixpath.join(base, i) for i in fnmatch.filter(files, name))

    for p in iterate(paths):
        if type != 'f' and fnmatch.fnmatch(p, name):
            results.append(p)

        generator = walker(p)
        for path, dirs, files in generator:
            if filter:
                _filter_in_place(dirs, 'd', filter)
                _filter_in_place(files, 'f', filter)

            seen_dirs.append(path)
            if type != 'f':
                results.extend(_filter_join(path, dirs, name))
            if type != 'd':
                results.extend(_filter_join(path, files, name))

    return results, seen_dirs

def find(path='.', name='*', type=None, flat=False):
    return _find_files(path, name, type, flat, None)[0]

known_platforms = ['posix', 'linux', 'darwin', 'cygwin', 'windows']

@builtin.globals('env')
def filter_by_platform(env, name, type):
    my_plat = set([env.platform.name, env.platform.kind])
    ex = '|'.join(re.escape(i) for i in known_platforms if i not in my_plat)
    return re.search(r'(^|_)(' + ex + r')(\.[^\.])?$', name) is None

@builtin.globals('builtins', 'build_inputs', 'env')
def find_files(builtins, build_inputs, env, path='.', name='*', type=None,
               flat=False, filter=filter_by_platform, cache=True):
    if filter == filter_by_platform:
        filter = builtins['filter_by_platform']

    results, seen_dirs = _find_files(path, name, type, flat, filter)
    if cache:
        build_inputs.find_dirs.update(seen_dirs)
    return results
