import fnmatch
import os
import posixpath
import re
from enum import IntEnum

from . import builtin
from ..file_types import File, Directory
from ..iterutils import iterate, listify
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..backends.make.syntax import Writer, Syntax
from ..build_inputs import build_input
from ..path import Path, Root
from ..platforms import known_platforms

build_input('find_dirs')(lambda build_inputs, env: set())
depfile_name = '.bfg_find_deps'
exclude_globs = ['.*#', '*~', '#*#']


@builtin.function()
class FindResult(IntEnum):
    include = 0
    not_now = 1
    exclude = 2


def write_depfile(env, path, output, seen_dirs, makeify=False):
    with open(path.string(env.base_dirs), 'w') as f:
        # Since this file is in the build dir, we can use relative dirs for
        # deps also in the build dir.
        roots = env.base_dirs.copy()
        roots[Root.builddir] = None

        out = Writer(f)
        out.write(output.string(roots), Syntax.target)
        out.write_literal(':')
        for i in seen_dirs:
            out.write_literal(' ')
            out.write(i.string(roots), Syntax.dependency)
        out.write_literal('\n')
        if makeify:
            for i in seen_dirs:
                out.write(i.string(roots), Syntax.target)
                out.write_literal(':\n')


def _listdir(path):
    dirs, nondirs = [], []
    try:
        names = os.listdir(path)
        for name in names:
            # Use POSIX paths so that the result is platform-agnostic.
            curpath = posixpath.join(path, name)
            if os.path.isdir(curpath):
                dirs.append((name, curpath))
            else:
                nondirs.append((name, curpath))
    except Exception:
        pass
    return dirs, nondirs


def _walk_flat(top):
    if os.path.exists(top):
        yield (top,) + _listdir(top)


def _walk_recursive(top):
    if not os.path.exists(top):
        return
    dirs, nondirs = _listdir(top)
    yield top, dirs, nondirs
    for name, path in dirs:
        if not os.path.islink(path):
            for i in _walk_recursive(path):
                yield i


def _filter_from_glob(match_type, matches, extra, exclude):
    matches = [re.compile(fnmatch.translate(i)) for i in iterate(matches)]
    extra = [re.compile(fnmatch.translate(i)) for i in iterate(extra)]
    exclude = [re.compile(fnmatch.translate(i)) for i in iterate(exclude)]

    def fn(name, path, type):
        if match_type in {type, '*'}:
            if any(ex.match(name) for ex in exclude):
                return FindResult.exclude
            if any(ex.match(name) for ex in matches):
                return FindResult.include
            elif any(ex.match(name) for ex in extra):
                return FindResult.not_now
        return FindResult.exclude
    return fn


def _find_files(paths, filter, flat, as_object):
    # "Does the walker choose the path, or the path the walker?" - Garth Nix
    walker = _walk_flat if flat else _walk_recursive

    results, dist_results, seen_dirs = [], [], []
    filetype = File if isinstance(as_object, bool) else as_object

    def do_filter(files, type):
        cls = filetype if type == 'f' else lambda p: Directory(p, None)
        for name, path in files:
            fileobj = cls(Path(path, Root.srcdir))
            matched = filter(name, path, type)
            if matched == FindResult.include:
                dist_results.append(fileobj)
                results.append(fileobj if as_object else path)
            elif matched == FindResult.not_now:
                dist_results.append(fileobj)

    do_filter(( (os.path.basename(p), p) for p in paths ), 'd')
    for p in paths:
        for base, dirs, files in walker(p):
            seen_dirs.append(Path(base, Root.srcdir))

            do_filter(dirs, 'd')
            do_filter(files, 'f')

    return results, dist_results, seen_dirs


def find(path='.', name='*', type='*', extra=None, exclude=exclude_globs,
         flat=False):
    glob_filter = _filter_from_glob(type, name, extra, exclude)
    return _find_files(listify(path), glob_filter, flat, False)[0]


@builtin.function('env')
def filter_by_platform(env, name, path, type):
    my_plat = {env.target_platform.genus, env.target_platform.family}
    sub = '|'.join(re.escape(i) for i in known_platforms if i not in my_plat)
    ex = r'(^|/|_)(' + sub + r')(\.[^\.]$|$|/)'
    return FindResult.not_now if re.search(ex, path) else FindResult.include


@builtin.function('builtins', 'build_inputs', 'env')
def find_files(builtins, build_inputs, env, path='.', name='*', type='*',
               extra=None, exclude=exclude_globs, filter=filter_by_platform,
               flat=False, cache=True, dist=True, as_object=False):
    glob_filter = _filter_from_glob(type, name, extra, exclude)
    if filter:
        if filter == filter_by_platform:
            filter = builtins['filter_by_platform']

        def final_filter(name, path, type):
            return max(filter(name, path, type), glob_filter(name, path, type))
    else:
        final_filter = glob_filter

    paths = [i.path.string(env.base_dirs) if isinstance(i, File) else i
             for i in iterate(path)]
    found, dist, seen_dirs = _find_files(paths, final_filter, flat, as_object)

    if cache:
        build_inputs['find_dirs'].update(seen_dirs)
        build_inputs['regenerate'].depfile = depfile_name
    if dist:
        for i in dist:
            build_inputs.add_source(i)
    return found


@make.post_rule
def make_find_dirs(build_inputs, buildfile, env):
    if build_inputs['find_dirs']:
        write_depfile(env, Path(depfile_name), make.filepath,
                      build_inputs['find_dirs'], makeify=True)
        buildfile.include(depfile_name)


@ninja.post_rule
def ninja_find_dirs(build_inputs, buildfile, env):
    if build_inputs['find_dirs']:
        write_depfile(env, Path(depfile_name), ninja.filepath,
                      build_inputs['find_dirs'])
