from contextlib import contextmanager

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


def static_file(context, file_type, name, dist=True, params=[], kwargs={}):
    extra_args = []
    for key, default in params:
        extra_args.append(kwargs.pop(key, default))
    if kwargs:
        raise TypeError("unexpected keyword argument '{}'".format(
            next(iter(kwargs))
        ))

    path = context['relpath'](name)
    file = file_type(path, *extra_args)
    if dist and path.root == Root.srcdir:
        context.build.add_source(file)
    return file


class FileList(list):
    def __init__(self, context, fn, files, **kwargs):
        super().__init__(fn(i, **kwargs) for i in iterate(files))
        self._relpath = context['relpath']

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self._relpath(key)
        elif isinstance(key, File):
            key = key.path

        if isinstance(key, Path):
            for i in self:
                if i.creator and i.creator.file.path == key:
                    return i
            raise IndexError('{!r} not found'.format(key))
        else:
            return super().__getitem__(key)


@contextmanager
def make_immediate_file(context, file, mode='w', makedirs=True):
    if makedirs:
        _makedirs(file.path.parent().string(context.env.base_dirs),
                  exist_ok=True)

    yield open(file.path.string(context.env.base_dirs), mode)
    context.build['regenerate'].outputs.append(file)


@builtin.function()
@builtin.type(File)
def generic_file(context, name, *, dist=True):
    return static_file(context, File, name, dist)


@builtin.function()
@builtin.type(SourceFile)
def source_file(context, name, lang=None, *, dist=True):
    path = context['relpath'](name)
    lang = lang or known_langs.fromext(path.ext(), 'source')
    return static_file(context, SourceFile, path, dist, [('lang', lang)])


@builtin.function()
@builtin.type(ResourceFile)
def resource_file(context, name, lang=None, *, dist=True):
    path = context['relpath'](name)
    lang = lang or known_langs.fromext(path.ext(), 'resource')
    return static_file(context, ResourceFile, path, dist, [('lang', lang)])


@builtin.function()
@builtin.type(HeaderFile)
def header_file(context, name, lang=None, *, dist=True):
    path = context['relpath'](name)
    lang = lang or known_langs.fromext(path.ext(), 'header')
    return static_file(context, HeaderFile, path, dist, [('lang', lang)])


@builtin.function()
@builtin.type(ModuleDefFile)
def module_def_file(context, name, *, dist=True):
    return static_file(context, ModuleDefFile, name, dist)


@builtin.function()
@builtin.type(File)
def auto_file(context, name, lang=None, *, dist=True):
    path = context['relpath'](name)
    if lang:
        kind = None
        if lang in known_langs:
            kind = known_langs[lang].extkind(path.ext())
    else:
        lang, kind = known_langs.extinfo(path.ext())

    if lang:
        return static_file(context, _kind_to_file_type[kind or 'source'], path,
                           dist, [('lang', lang)])
    return static_file(context, File, path, dist)


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.


def _find(context, path, include, type, extra, *args, **kwargs):
    if not include and not extra:
        return None
    return context['find_files'](path, include, type, extra, *args, **kwargs)


def _directory_path(context, thing):
    if isinstance(thing, File):
        return thing.path.parent()
    else:
        return context['relpath'](thing)


@builtin.function()
@builtin.type(Directory, extra_in_type=File)
def directory(context, name, include=None, extra=None, exclude=exclude_globs,
              filter=None, *, dist=True, cache=True):
    path = _directory_path(context, name)
    files = _find(context, path, include, '*', extra, exclude, filter,
                  dist=dist, cache=cache)
    return static_file(context, Directory, path, dist, [('files', files)])


@builtin.function()
@builtin.type(HeaderDirectory, extra_in_type=SourceCodeFile)
def header_directory(context, name, include=None, extra=None,
                     exclude=exclude_globs, filter=None, system=False,
                     lang=None, *, dist=True, cache=True):
    def header_file(*args, **kwargs):
        return context['header_file'](*args, lang=lang, **kwargs)

    if isinstance(name, SourceCodeFile):
        lang = name.lang

    path = _directory_path(context, name)
    files = _find(context, path, include, 'f', extra, exclude, filter,
                  file_type=header_file, dist=dist, cache=cache)
    langs = uniques(i.lang for i in files if i.lang) if files else lang

    params = [('files', files), ('system', system), ('langs', langs)]
    return static_file(context, HeaderDirectory, path, dist, params)
