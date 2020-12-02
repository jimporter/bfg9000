import re
from enum import Enum
from functools import reduce

from . import builtin
from ..glob import NameGlob, PathGlob
from ..iterutils import iterate, listify
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..backends.make.syntax import Writer, Syntax
from ..build_inputs import build_input
from ..path import Path, Root, walk, uniquetrees
from ..platforms import known_platforms

build_input('find_dirs')(lambda build_inputs, env: set())
depfile_name = '.bfg_find_deps'


@builtin.default()
class FindResult(Enum):
    include = 0
    not_now = 1
    exclude = 2
    exclude_recursive = 3

    def __bool__(self):
        return self == self.include

    def __and__(self, rhs):
        return type(self)(max(self.value, rhs.value))

    def __or__(self, rhs):
        return type(self)(min(self.value, rhs.value))


class FileFilter:
    def __init__(self, include, type=None, extra=None, exclude=None,
                 filter_fn=None):
        self.include = [PathGlob(i, type) for i in iterate(include)]
        if not self.include:
            raise ValueError('at least one pattern required')
        self.extra = [NameGlob(i, type) for i in iterate(extra)]
        self.exclude = [NameGlob(i, type) for i in iterate(exclude)]
        self.filter_fn = filter_fn

    def bases(self):
        return uniquetrees([i.base for i in self.include])

    def _match_globs(self, path):
        if any(i.match(path) for i in self.exclude):
            return FindResult.exclude_recursive

        skip_base = len(self.include) == 1
        result = reduce(lambda a, b: a | b,
                        (i.match(path, skip_base) for i in self.include))
        if result:
            return FindResult.include

        if any(i.match(path) for i in self.extra):
            return FindResult.not_now

        if result == PathGlob.Result.never:
            return FindResult.exclude_recursive
        return FindResult.exclude

    def match(self, path):
        result = self._match_globs(path)
        if self.filter_fn:
            return result & self.filter_fn(path)
        return result


def write_depfile(env, path, output, seen_dirs, makeify=False):
    with open(path.string(env.base_dirs), 'w') as f:
        # Since this file is in the build dir, we can use relative dirs for
        # deps also in the build dir.
        roots = env.base_dirs.copy()
        roots[Root.builddir] = None

        out = Writer(f, None)
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


def _path_type(path):
    return 'd' if path.directory else 'f'


@builtin.function()
def filter_by_platform(context, path):
    env = context.env
    my_plat = {env.target_platform.genus, env.target_platform.family}

    sub = '|'.join(re.escape(i) for i in known_platforms if i not in my_plat)
    ex = r'(^|/|_)(' + sub + r')(\.[^\.]+$|$|/)'
    return (FindResult.not_now if re.search(ex, path.suffix)
            else FindResult.include)


def _find_files(env, filter, seen_dirs=None):
    paths = filter.bases()

    for p in paths:
        yield p, filter.match(p)
    for p in paths:
        for base, dirs, files in walk(p, env.base_dirs):
            if seen_dirs is not None:
                seen_dirs.append(base)
            to_remove = []

            for i, p in enumerate(dirs):
                m = filter.match(p)
                if m == FindResult.exclude_recursive:
                    to_remove.append(i)
                yield p, m
            for p in files:
                yield p, filter.match(p)

            for i in reversed(to_remove):
                del dirs[i]


def find(env, pattern, type=None, extra=None, exclude=None):
    pattern = [Path.ensure(i, Root.srcdir) for i in iterate(pattern)]
    file_filter = FileFilter(pattern, type, extra, exclude)

    results = []
    for path, matched in _find_files(env, file_filter):
        if matched == FindResult.include:
            results.append(path)
    return results


@builtin.function()
def find_files(context, pattern, *, type=None, extra=None, exclude=None,
               filter=None, file_type=None, dir_type=None, dist=True,
               cache=True):
    types = {'f': file_type or context['auto_file'],
             'd': dir_type or context['directory']}
    extra_types = {'f': context['generic_file'], 'd': context['directory']}

    pattern = [context['relpath'](i) for i in iterate(pattern)]
    exclude = context.build['project']['find_exclude'] + listify(exclude)
    file_filter = FileFilter(pattern, type, extra, exclude, filter)

    found, seen_dirs = [], []
    for path, matched in _find_files(context.env, file_filter, seen_dirs):
        if matched == FindResult.include:
            found.append(types[_path_type(path)](path, dist=dist))
        elif matched == FindResult.not_now and dist:
            extra_types[_path_type(path)](path, dist=dist)

    if cache:
        context.build['find_dirs'].update(seen_dirs)
        context.build['regenerate'].depfile = depfile_name
    return found


@builtin.function()
def find_paths(context, *args, **kwargs):
    return [i.path for i in context['find_files'](*args, **kwargs)]


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
