import json
import os
import re
from collections import namedtuple
from collections.abc import Mapping
from enum import Enum
from functools import reduce

from . import builtin, regenerate
from .. import path as _path
from ..exceptions import SerializationError
from ..glob import NameGlob, PathGlob
from ..iterutils import iterate, listify
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..backends.make.syntax import Writer, Syntax
from ..build_inputs import build_input, Regenerating
from ..exceptions import AbortConfigure
from ..path import Path, Root
from ..platforms import known_platforms

build_input('find_dirs')(set)
depfile_name = '.bfg_find_deps'


@build_input('find_cache')
class FindCache(Mapping):
    FindCacheEntry = namedtuple('FindCacheEntry', ['found', 'extra'])

    def __init__(self):
        self._cache = {}

    def to_json(self):
        return [
            [file_filter.to_json(),
             *[[i.to_json() for i in matches] for matches in cache]]
            for file_filter, cache in self._cache.items()
        ]

    @classmethod
    def from_json(cls, data, context):
        cache = cls.__new__(cls)
        cache._cache = {
            FileFilter.from_json(k, context):
            cls.FindCacheEntry._make([Path.from_json(i) for i in matches]
                                     for matches in v)
            for k, *v in data
        }
        return cache

    def add(self, file_filter, found, extra):
        assert file_filter not in self._cache

        self._cache[file_filter] = self.FindCacheEntry(found, extra)

    def __getitem__(self, file_filter):
        return self._cache[file_filter]

    def __iter__(self):
        return iter(self._cache)

    def __len__(self):
        return len(self._cache)

    def __repr__(self):
        return repr(self._cache)


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
        self.include = tuple(PathGlob(i, type) for i in iterate(include))
        if not self.include:
            raise ValueError('at least one pattern required')
        self.extra = tuple(NameGlob(i, type) for i in iterate(extra))
        self.exclude = tuple(NameGlob(i, type) for i in iterate(exclude))
        self.filter_fn = filter_fn

    def to_json(self):
        # We can only serialize built-in filter functions. Arbitrary functions
        # would require re-running the entire `build.bfg`.
        if self.filter_fn and not hasattr(self.filter_fn, '_builtin_name'):
            raise SerializationError('filter_fn')

        return {'include': [i.to_json() for i in self.include],
                'extra':   [i.to_json() for i in self.extra],
                'exclude': [i.to_json() for i in self.exclude],
                'filter_fn': (self.filter_fn._builtin_name if self.filter_fn
                              else None)}

    @classmethod
    def from_json(cls, data, context):
        f = cls.__new__(cls)
        f.include = tuple(PathGlob.from_json(i) for i in data['include'])
        f.extra = tuple(NameGlob.from_json(i) for i in data['extra'])
        f.exclude = tuple(NameGlob.from_json(i) for i in data['exclude'])
        try:
            f.filter_fn = (context[data['filter_fn']] if data['filter_fn']
                           else None)
        except KeyError as e:
            raise SerializationError(str(e))
        return f

    def bases(self):
        return _path.uniquetrees([i.base for i in self.include])

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

    def __eq__(self, rhs):
        return (self.include == rhs.include and self.extra == rhs.extra and
                self.exclude == rhs.exclude and
                self.filter_fn == rhs.filter_fn)

    def __ne__(self, rhs):
        return not (self == rhs)

    def __hash__(self):
        return hash((self.include, self.extra, self.exclude, self.filter_fn))

    def __repr__(self):
        return (
            'FileFilter(include={}, extra={}, exclude={}, filter_fn={})'
            .format(self.include, self.extra, self.exclude, self.filter_fn)
        )


class CacheVersionError(RuntimeError):
    pass


class FindCacheFile(namedtuple('FindCacheFile', ['regen_files', 'cache'])):
    version = 1
    cachefile = '.bfg_find_cache'

    def save(self, path):
        if self.cache:
            try:
                data = {
                    'version': self.version,
                    'data': {
                        'regen_files': self.regen_files.to_json(),
                        'cache': self.cache.to_json(),
                    }
                }
                with open(os.path.join(path, self.cachefile), 'w') as out:
                    json.dump(data, out)
                return
            except SerializationError:
                pass

        try:
            os.remove(os.path.join(path, self.cachefile))
        except FileNotFoundError:  # pragma: no cover
            pass

    @classmethod
    def load(cls, path, context):
        with open(os.path.join(path, cls.cachefile)) as inp:
            state = json.load(inp)
            version, data = state['version'], state['data']
        if version > cls.version:
            raise CacheVersionError('saved version exceeds expected version')

        return cls(regenerate.RegenerateFiles.from_json(data['regen_files']),
                   FindCache.from_json(data['cache'], context))


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
        for base, dirs, files in _path.walk(p, env.base_dirs):
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

    found = []
    for path, matched in _find_files(env, file_filter):
        if matched == FindResult.include:
            found.append(path)
    return found


def find_from_filter(context, file_filter, *, file_type=None, dir_type=None,
                     dist=True, cache=True):
    types = {'f': file_type or context['auto_file'],
             'd': dir_type or context['directory']}
    extra_types = {'f': context['generic_file'], 'd': context['directory']}

    if cache:
        try:
            return [types[_path_type(i)](i, dist=dist) for i in
                    context.build['find_cache'][file_filter].found]
        except KeyError:
            pass

    results, found, extra, seen_dirs = [], [], [], []
    for path, matched in _find_files(context.env, file_filter, seen_dirs):
        if matched == FindResult.include:
            if cache:
                found.append(path)
            results.append(types[_path_type(path)](path, dist=dist))
        elif matched == FindResult.not_now:
            if cache:
                extra.append(path)
            extra_types[_path_type(path)](path, dist=dist)

    if cache:
        context.build['find_cache'].add(file_filter, found, extra)
        context.build['find_dirs'].update(seen_dirs)
    return results


@builtin.function()
def find_files(context, pattern, *, type=None, extra=None, exclude=None,
               filter=None, cache=True, **kwargs):
    pattern = tuple(context['relpath'](i) for i in iterate(pattern))
    exclude = context.build['project']['find_exclude'] + listify(exclude)
    file_filter = FileFilter(pattern, type, extra, exclude, filter)

    if cache:
        # Do this here instead of `find_from_filter` since that function is
        # also called when checking cached find results during regeneration. If
        # the current contents of `build.bfg` don't have any `find_files`
        # calls, we don't want to add the depfile, even if the *previous*
        # contents of `build.bfg` had some.
        context.build['regenerate'].depfile = depfile_name

    return find_from_filter(context, file_filter, cache=cache, **kwargs)


@builtin.function()
def find_paths(context, *args, **kwargs):
    # We call `find_files` here instead of the other way around because we want
    # to be sure that if we add files to the dist, they're proper file objects
    # (instead of just path objects). This probably isn't strictly necessary,
    # but it's more conceptually correct.
    return [i.path for i in context['find_files'](*args, **kwargs)]


@builtin.pre_execute_hook()
def find_check_cache(context):
    if context.regenerating is not Regenerating.lazy:
        return

    try:
        regen_files, old_cache = FindCacheFile.load(
            context.env.builddir.string(), context
        )
    except FileNotFoundError:
        return

    # Check if any of the explicit inputs are newer than any of the explicit
    # outputs. If so, we definitely want to regenerate the build files.
    if ( max(_path.getmtime_ns(i, context.env.base_dirs, strict=False)
             for i in regen_files.inputs) >
         min(_path.getmtime_ns(i, context.env.base_dirs, strict=False)
             for i in regen_files.outputs) ):
        return

    # Otherwise, check to see if any of the `find_files` calls have different
    # results. If not, we can avoid regenerating.
    regenerate = False

    for file_filter, results in old_cache.items():
        found, extra, seen_dirs = [], [], []
        for path, matched in _find_files(context.env, file_filter, seen_dirs):
            if matched == FindResult.include:
                found.append(path)
            elif matched == FindResult.not_now:
                extra.append(path)

        regenerate = regenerate or results[0] != found or results[1] != extra
        # Fill in the find cache with our results so that if/when we actually
        # regenerate our build files, we can just reuse the cached values.
        context.build['find_cache'].add(file_filter, found, extra)
        context.build['find_dirs'].update(seen_dirs)

    if not regenerate:
        # We don't want to regenerate. To make sure the build backend is happy,
        # update the modification time of all the output files.
        for i in regen_files.outputs:
            if _path.exists(i, context.env.base_dirs):
                _path.touch(i, context.env.base_dirs)
        raise AbortConfigure()


@make.post_rules_hook
def make_find_dirs(build_inputs, buildfile, env):
    if build_inputs['find_dirs']:
        write_depfile(env, Path(depfile_name), make.filepath,
                      build_inputs['find_dirs'], makeify=True)
        buildfile.include(depfile_name)

    FindCacheFile(
        regenerate.RegenerateFiles.make(build_inputs, env),
        build_inputs['find_cache']
    ).save(env.builddir.string())


@ninja.post_rules_hook
def ninja_find_dirs(build_inputs, buildfile, env):
    if build_inputs['find_dirs']:
        write_depfile(env, Path(depfile_name), ninja.filepath,
                      build_inputs['find_dirs'])

    FindCacheFile(
        regenerate.RegenerateFiles.make(build_inputs, env),
        build_inputs['find_cache']
    ).save(env.builddir.string())
