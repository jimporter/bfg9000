import fnmatch
import os
import re
from enum import IntEnum

from . import builtin
from ..file_types import File
from ..iterutils import iterate
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..backends.make.syntax import Writer, Syntax
from ..build_inputs import build_input
from ..path import exists, isdir, islink, Path, Root
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


def _listdir(path, variables=None):
    dirs, nondirs = [], []
    try:
        names = os.listdir(path.string(variables))
        for name in names:
            curpath = path.append(name)
            if isdir(curpath, variables):
                dirs.append(curpath)
            else:
                nondirs.append(curpath)
    except OSError:
        pass
    return dirs, nondirs


def _walk_flat(top, variables=None):
    if exists(top, variables):
        yield (top,) + _listdir(top, variables)


def _walk_recursive(top, variables=None):
    if not exists(top, variables):
        return
    dirs, nondirs = _listdir(top, variables)
    yield top, dirs, nondirs
    for d in dirs:
        if not islink(d, variables):
            for i in _walk_recursive(d, variables):
                yield i


def _make_filter_from_glob(match_type, matches, extra, exclude):
    matches = [re.compile(fnmatch.translate(i)) for i in iterate(matches)]
    extra = [re.compile(fnmatch.translate(i)) for i in iterate(extra)]
    exclude = [re.compile(fnmatch.translate(i)) for i in iterate(exclude)]

    def fn(path, type):
        name = path.basename()
        if match_type in {type, '*'}:
            if any(ex.match(name) for ex in exclude):
                return FindResult.exclude
            if any(ex.match(name) for ex in matches):
                return FindResult.include
            elif any(ex.match(name) for ex in extra):
                return FindResult.not_now
        return FindResult.exclude
    return fn


@builtin.function('env')
def filter_by_platform(env, path, type):
    my_plat = {env.target_platform.genus, env.target_platform.family}
    sub = '|'.join(re.escape(i) for i in known_platforms if i not in my_plat)
    ex = r'(^|/|_)(' + sub + r')(\.[^\.]+$|$|/)'
    return (FindResult.not_now if re.search(ex, path.suffix)
            else FindResult.include)


def _combine_filters(*args):
    return lambda path, type: max(f(path, type) for f in args)


def _find_files(env, paths, filter, flat, seen_dirs=None):
    # "Does the walker choose the path, or the path the walker?" - Garth Nix
    walker = _walk_flat if flat else _walk_recursive

    for p in paths:
        yield p, 'd', filter(p, 'd')
    for p in paths:
        for base, dirs, files in walker(p, env.base_dirs):
            if seen_dirs is not None:
                seen_dirs.append(base)

            for p in dirs:
                yield p, 'd', filter(p, 'd')
            for p in files:
                yield p, 'f', filter(p, 'f')


def find(env, path='.', name='*', type='*', extra=None, exclude=exclude_globs,
         flat=False):
    glob_filter = _make_filter_from_glob(type, name, extra, exclude)
    paths = [Path.ensure(i, Root.srcdir) for i in iterate(path)]

    results = []
    for path, type, matched in _find_files(env, paths, glob_filter, flat):
        if matched == FindResult.include:
            results.append(path)
    return results


@builtin.function('builtins', 'build_inputs', 'env')
def find_files(builtins, build_inputs, env, path='.', name='*', type='*',
               extra=None, exclude=exclude_globs, filter=None, flat=False,
               file_type=None, dir_type=None, dist=True, cache=True):
    final_filter = _make_filter_from_glob(type, name, extra, exclude)
    if filter:
        final_filter = _combine_filters(final_filter, filter)

    types = {'f': file_type or builtins['auto_file'],
             'd': dir_type or builtins['directory']}
    extra_types = {'f': builtins['generic_file'], 'd': builtins['directory']}

    paths = [i.path if isinstance(i, File) else Path.ensure(i, Root.srcdir)
             for i in iterate(path)]

    found, seen_dirs = [], []
    for path, type, matched in _find_files(env, paths, final_filter, flat,
                                           seen_dirs):
        if matched == FindResult.include:
            found.append(types[type](path, dist=dist))
        elif matched == FindResult.not_now and dist:
            extra_types[type](path, dist=dist)

    if cache:
        build_inputs['find_dirs'].update(seen_dirs)
        build_inputs['regenerate'].depfile = depfile_name
    return found


@builtin.function('builtins')
def find_paths(builtins, *args, **kwargs):
    return [i.path for i in builtins['find_files'](*args, **kwargs)]


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
