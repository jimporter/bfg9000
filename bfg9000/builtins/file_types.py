from contextlib import contextmanager

from . import builtin
from .find import exclude_globs, filter_by_platform
from ..file_types import *
from ..iterutils import iterate, uniques
from ..languages import known_langs
from ..path import Path, Root, makedirs as _makedirs

_kind_to_file_type = {
    'header': HeaderFile,
    'source': SourceFile,
}


def static_file(build, file_type, name, params=[], kwargs={}):
    extra_args = []
    for key, default in params:
        extra_args.append(kwargs.pop(key, default))
    if kwargs:
        raise TypeError("unexpected keyword argument '{}'".format(
            next(iter(kwargs))
        ))

    path = Path.ensure(name, Root.srcdir)
    file = file_type(path, *extra_args)
    if path.root == Root.srcdir:
        build.add_source(file)
    return file


@contextmanager
def generated_file(build, env, file, mode='w', makedirs=True):
    if makedirs:
        _makedirs(file.path.parent().string(env.base_dirs), exist_ok=True)

    yield open(file.path.string(env.base_dirs), mode)
    build['regenerate'].outputs.append(file)


@builtin.function('build_inputs')
@builtin.type(File)
def generic_file(build, name):
    return static_file(build, File, name)


@builtin.function('build_inputs')
@builtin.type(SourceFile)
def source_file(build, name, lang=None):
    path = Path.ensure(name, Root.srcdir)
    lang = lang or known_langs.fromext(path.ext(), 'source')
    return static_file(build, SourceFile, path, [('lang', lang)])


@builtin.function('build_inputs')
@builtin.type(HeaderFile)
def header_file(build, name, lang=None):
    path = Path.ensure(name, Root.srcdir)
    lang = lang or known_langs.fromext(path.ext(), 'header')
    return static_file(build, HeaderFile, path, [('lang', lang)])


@builtin.function('build_inputs')
@builtin.type(ModuleDefFile)
def module_def_file(build, name):
    return static_file(build, ModuleDefFile, name)


@builtin.function('build_inputs')
@builtin.type(File)
def auto_file(build, name, lang=None):
    path = Path.ensure(name, Root.srcdir)
    if lang:
        kind = None
        if lang in known_langs:
            kind = known_langs[lang].extkind(path.ext())
    else:
        lang, kind = known_langs.extinfo(path.ext())

    if lang:
        return static_file(build, _kind_to_file_type[kind or 'source'], path,
                           [('lang', lang)])
    return static_file(build, File, path)


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.


def _find(builtins, name, include, type, exclude, filter, as_object=True):
    if not include:
        return None
    return builtins['find_files'](name, include, type, None, exclude, filter,
                                  as_object=as_object)


@builtin.function('builtins', 'build_inputs')
@builtin.type(Directory, extra_in_type=File)
def directory(builtins, build, name, include=None, exclude=exclude_globs,
              filter=filter_by_platform):
    if isinstance(name, File):
        path = name.path.parent()
    else:
        path = Path(name, Root.srcdir)

    files = _find(builtins, name, include, '*', exclude, filter)
    return Directory(path, files)


@builtin.function('builtins', 'build_inputs')
@builtin.type(HeaderDirectory, extra_in_type=CodeFile)
def header_directory(builtins, build, name, include=None,
                     exclude=exclude_globs, filter=filter_by_platform,
                     system=False, lang=None):
    if isinstance(name, HeaderFile):
        path = name.path.parent()
        lang = name.lang
    else:
        path = Path(name, Root.srcdir)

    files = _find(builtins, name, include, 'f', exclude, filter,
                  lambda p: HeaderFile(p, lang))
    langs = (uniques(i.lang for i in files if i.lang)
             if files else iterate(lang))
    return HeaderDirectory(path, files, system, langs)
