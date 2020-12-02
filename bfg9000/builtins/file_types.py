import os
from collections import abc
from contextlib import contextmanager
from itertools import chain

from . import builtin
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..languages import known_langs
from ..path import Path, Root

_kind_to_file_type = {
    'header': HeaderFile,
    'source': SourceFile,
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


class FileList(abc.Sequence):
    def __init__(self, relpath, files):
        self.__files = listify(files, scalar_ok=False)
        self.__relpath = relpath

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.__relpath(key)
        elif isinstance(key, FileOrDirectory):
            key = key.path

        if isinstance(key, Path):
            for i in self.__files:
                if i.creator and i.creator.file.path == key:
                    return i
            raise IndexError('{!r} not found'.format(key))
        else:
            return self.__files[key]

    def __len__(self):
        return len(self.__files)

    def __add__(self, rhs):
        return list(chain(self.__files, rhs))

    def __radd__(self, lhs):
        return list(chain(lhs, self.__files))

    def __eq__(self, rhs):
        return rhs == self.__files

    def __repr__(self):
        return 'FileList({!r})'.format(self.__files)


def make_file_list(context, fn, files, **kwargs):
    return FileList(context['relpath'],
                    [fn(i, **kwargs) for i in iterate(files)])


@contextmanager
def make_immediate_file(context, file, mode='w', makedirs=True):
    if makedirs:
        os.makedirs(file.path.parent().string(context.env.base_dirs),
                    exist_ok=True)

    with open(file.path.string(context.env.base_dirs), mode) as f:
        yield f
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
    if path.directory:
        file_type = HeaderDirectory if lang else Directory
    else:
        if lang:
            kind = None
            if lang in known_langs:
                src_lang = known_langs[lang].src_lang
                kind = known_langs[src_lang].extkind(path.ext())
        else:
            lang, kind = known_langs.extinfo(path.ext())

        file_type = _kind_to_file_type[kind or 'source'] if lang else File

    params = [('lang', lang)] if lang else []
    return static_file(context, file_type, path, dist, params)


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.


def _find(context, path, include, **kwargs):
    if not include:
        return None

    patterns = [path.append(i) for i in iterate(include)]
    return context['find_files'](patterns, **kwargs)


def _directory_path(context, thing):
    if isinstance(thing, File):
        return thing.path.parent()
    else:
        return context['relpath'](thing)


@builtin.function()
@builtin.type(Directory, extra_in_type=File)
def directory(context, name, include=None, *, dist=True, **kwargs):
    path = _directory_path(context, name)
    files = _find(context, path, include, type='*', dist=dist, **kwargs)
    return static_file(context, Directory, path, dist, [('files', files)])


@builtin.function()
@builtin.type(HeaderDirectory, extra_in_type=CodeFile)
def header_directory(context, name, include=None, lang=None, *, system=False,
                     dist=True, **kwargs):
    def header_file(*args, **kwargs):
        return context['header_file'](*args, lang=lang, **kwargs)

    if isinstance(name, CodeFile):
        lang = name.lang

    path = _directory_path(context, name)
    files = _find(context, path, include, type='f', dist=dist, **kwargs)
    langs = uniques(i.lang for i in files if i.lang) if files else lang

    params = [('files', files), ('system', system), ('langs', langs)]
    return static_file(context, HeaderDirectory, path, dist, params)
