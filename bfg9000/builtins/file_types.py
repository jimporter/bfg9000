from contextlib import contextmanager
from six import string_types

from . import builtin
from .find import exclude_globs
from ..file_types import *
from ..iterutils import iterate, uniques
from ..languages import known_langs
from ..path import Path, Root, makedirs as _makedirs

_kind_to_file_type = {
    'header': HeaderFile,
    'source': SourceFile,
    'resource': ResourceFile,
}


def static_file(build, file_type, name, dist=True, params=[], kwargs={}):
    extra_args = []
    for key, default in params:
        extra_args.append(kwargs.pop(key, default))
    if kwargs:
        raise TypeError("unexpected keyword argument '{}'".format(
            next(iter(kwargs))
        ))

    path = Path.ensure(name, Root.srcdir)
    file = file_type(path, *extra_args)
    if dist and path.root == Root.srcdir:
        build.add_source(file)
    return file


class FileList(list):
    def __init__(self, fn, files, **kwargs):
        list.__init__(self, (fn(i, **kwargs) for i in iterate(files)))

    def __getitem__(self, key):
        if isinstance(key, string_types):
            key = Path(key, Root.srcdir)
        elif isinstance(key, File):
            key = key.path

        if isinstance(key, Path):
            for i in self:
                if i.creator and i.creator.file.path == key:
                    return i
            raise IndexError('{!r} not found'.format(key))
        else:
            return list.__getitem__(self, key)


@contextmanager
def make_immediate_file(build, env, file, mode='w', makedirs=True):
    if makedirs:
        _makedirs(file.path.parent().string(env.base_dirs), exist_ok=True)

    yield open(file.path.string(env.base_dirs), mode)
    build['regenerate'].outputs.append(file)


@builtin.function('build_inputs')
@builtin.type(File)
def generic_file(build, name, dist=True):
    return static_file(build, File, name, dist)


@builtin.function('build_inputs')
@builtin.type(SourceFile)
def source_file(build, name, lang=None, dist=True):
    path = Path.ensure(name, Root.srcdir)
    lang = lang or known_langs.fromext(path.ext(), 'source')
    return static_file(build, SourceFile, path, dist, [('lang', lang)])


@builtin.function('build_inputs')
@builtin.type(ResourceFile)
def resource_file(build, name, lang=None, dist=True):
    path = Path.ensure(name, Root.srcdir)
    lang = lang or known_langs.fromext(path.ext(), 'resource')
    return static_file(build, ResourceFile, path, dist, [('lang', lang)])


@builtin.function('build_inputs')
@builtin.type(HeaderFile)
def header_file(build, name, lang=None, dist=True):
    path = Path.ensure(name, Root.srcdir)
    lang = lang or known_langs.fromext(path.ext(), 'header')
    return static_file(build, HeaderFile, path, dist, [('lang', lang)])


@builtin.function('build_inputs')
@builtin.type(ModuleDefFile)
def module_def_file(build, name, dist=True):
    return static_file(build, ModuleDefFile, name, dist)


@builtin.function('build_inputs')
@builtin.type(File)
def auto_file(build, name, lang=None, dist=True):
    path = Path.ensure(name, Root.srcdir)
    if lang:
        kind = None
        if lang in known_langs:
            kind = known_langs[lang].extkind(path.ext())
    else:
        lang, kind = known_langs.extinfo(path.ext())

    if lang:
        return static_file(build, _kind_to_file_type[kind or 'source'], path,
                           dist, [('lang', lang)])
    return static_file(build, File, path, dist)


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.


def _find(builtins, path, include, type, extra, *args, **kwargs):
    if not include and not extra:
        return None
    return builtins['find_files'](path, include, type, extra, *args, **kwargs)


def _directory_path(thing):
    if isinstance(thing, File):
        return thing.path.parent()
    else:
        return Path.ensure(thing, Root.srcdir)


@builtin.function('builtins', 'build_inputs')
@builtin.type(Directory, extra_in_type=File)
def directory(builtins, build, name, include=None, extra=None,
              exclude=exclude_globs, filter=None, dist=True, cache=True):
    path = _directory_path(name)
    files = _find(builtins, path, include, '*', extra, exclude, filter,
                  dist=dist, cache=cache)
    return static_file(build, Directory, path, dist, [('files', files)])


@builtin.function('builtins', 'build_inputs')
@builtin.type(HeaderDirectory, extra_in_type=SourceCodeFile)
def header_directory(builtins, build, name, include=None, extra=None,
                     exclude=exclude_globs, filter=None, system=False,
                     lang=None, dist=True, cache=True):
    def header_file(*args, **kwargs):
        return builtins['header_file'](*args, lang=lang, **kwargs)

    if isinstance(name, SourceCodeFile):
        lang = name.lang

    path = _directory_path(name)
    files = _find(builtins, path, include, 'f', extra, exclude, filter,
                  file_type=header_file, dist=dist, cache=cache)
    langs = uniques(i.lang for i in files if i.lang) if files else lang

    params = [('files', files), ('system', system), ('langs', langs)]
    return static_file(build, HeaderDirectory, path, dist, params)
