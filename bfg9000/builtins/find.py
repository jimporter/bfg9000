import fnmatch
import os
import posixpath
import re

from .hooks import builtin
from ..iterutils import listify
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..backends.make.syntax import Writer, Syntax
from ..build_inputs import build_input
from ..path import Path
from ..platforms import known_platforms

build_input('find_dirs')(lambda build_inputs: set())
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
            # Use POSIX paths so that the result is platform-agnostic.
            curpath = posixpath.join(path, name)
            if os.path.isdir(curpath):
                dirs.append((name, curpath))
            else:
                nondirs.append((name, curpath))
    except:
        pass
    return dirs, nondirs


def _walk_flat(top):
    yield (top,) + _listdir(top)


def _walk_recursive(top):
    dirs, nondirs = _listdir(top)
    yield top, dirs, nondirs
    for name, path in dirs:
        if not os.path.islink(path):
            for i in _walk_recursive(path):
                yield i


def _filter_from_glob(match_name, match_type):
    regex = re.compile(fnmatch.translate(match_name))

    def f(name, path, type):
        return match_type in [type, '*'] and regex.match(name)
    return f


def _find_files(paths, filter, flat):
    def do_filter(files, type, filter):
        for name, path in files:
            if filter(name, path, type):
                yield path

    # "Does the walker choose the path, or the path the walker?" - Garth Nix
    walker = _walk_flat if flat else _walk_recursive

    results, seen_dirs = [], []

    paths = listify(paths)
    results.extend(do_filter( ((p, p) for p in paths), 'd', filter ))
    for p in paths:
        for base, dirs, files in walker(p):
            seen_dirs.append(base)

            results.extend(do_filter(dirs, 'd', filter))
            results.extend(do_filter(files, 'f', filter))

    return results, seen_dirs


def find(path='.', name='*', type='*', flat=False):
    return _find_files(path, _filter_from_glob(name, type), flat)[0]


@builtin.globals('env')
def filter_by_platform(env, name, path, type):
    my_plat = set([env.platform.name, env.platform.flavor])
    sub = '|'.join(re.escape(i) for i in known_platforms if i not in my_plat)
    ex = r'(^|/|_)(' + sub + r')(\.[^\.]$|$|/)'
    return re.search(ex, path) is None


@builtin.globals('builtins', 'build_inputs', 'env')
def find_files(builtins, build_inputs, env, path='.', name='*', type='*',
               filter=filter_by_platform, flat=False, cache=True):
    glob_filter = _filter_from_glob(name, type)
    if filter:
        if filter == filter_by_platform:
            filter = builtins['filter_by_platform']

        def final_filter(name, path, type):
            return filter(name, path, type) and glob_filter(name, path, type)
    else:
        final_filter = glob_filter

    results, seen_dirs = _find_files(path, final_filter, flat)
    if cache:
        build_inputs['find_dirs'].update(seen_dirs)
    return results


@make.post_rule
def make_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')
    bfgcmd = make.cmd_var(bfg9000, buildfile)

    if build_inputs['find_dirs']:
        write_depfile(Path(depfile_name).string(env.path_roots),
                      'Makefile', build_inputs['find_dirs'], makeify=True)
        buildfile.include(depfile_name)

    buildfile.rule(
        target=Path('Makefile'),
        deps=[build_inputs.bfgpath],
        recipe=[bfg9000.regenerate(bfgcmd, Path('.'))]
    )


@ninja.post_rule
def ninja_regenerate_rule(build_inputs, buildfile, env):
    bfg9000 = env.tool('bfg9000')
    bfgcmd = ninja.cmd_var(bfg9000, buildfile)
    depfile = None

    if build_inputs['find_dirs']:
        write_depfile(Path(depfile_name).string(env.path_roots),
                      'build.ninja', build_inputs['find_dirs'])
        depfile = depfile_name

    buildfile.rule(
        name='regenerate',
        command=bfg9000.regenerate(bfgcmd, Path('.')),
        generator=True,
        depfile=depfile,
    )
    buildfile.build(
        output=Path('build.ninja'),
        rule='regenerate',
        implicit=[build_inputs.bfgpath]
    )
