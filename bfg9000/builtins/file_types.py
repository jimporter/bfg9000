from contextlib import contextmanager
from six import string_types

from . import builtin
from .find import exclude_globs, filter_by_platform
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Path, Root, makedirs as _makedirs


def local_file(build, file_type, name, params, kwargs):
    extra_args = []
    for key, default in params:
        extra_args.append(kwargs.pop(key, default))
    if kwargs:
        raise TypeError("unexpected keyword argument '{}'".format(
            next(iter(kwargs))
        ))
    return build.add_source(file_type(Path(name, Root.srcdir), *extra_args))


@contextmanager
def generated_file(build, env, file, mode='w', makedirs=True):
    if makedirs:
        _makedirs(file.path.parent().string(env.base_dirs), exist_ok=True)

    yield open(file.path.string(env.base_dirs), mode)
    build['regenerate'].outputs.append(file)


@builtin.function('build_inputs')
@builtin.type(File)
def generic_file(build, name):
    return build.add_source(File(Path(name, Root.srcdir)))


@builtin.function('build_inputs')
@builtin.type(SourceFile)
def source_file(build, name, lang=None):
    return build.add_source(SourceFile(Path(name, Root.srcdir), lang))


@builtin.function('build_inputs')
@builtin.type(HeaderFile)
def header_file(build, name, lang=None):
    return build.add_source(HeaderFile(Path(name, Root.srcdir), lang))


@builtin.function('build_inputs')
@builtin.type(ModuleDefFile)
def module_def_file(build, name):
    return build.add_source(ModuleDefFile(Path(name, Root.srcdir)))


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
@builtin.type(Directory, in_type=string_types + (File,))
def directory(builtins, build, name, include=None, exclude=exclude_globs,
              filter=filter_by_platform):
    if isinstance(name, File):
        path = name.path.parent()
    else:
        path = Path(name, Root.srcdir)

    files = _find(builtins, name, include, '*', exclude, filter)
    return Directory(path, files)


@builtin.function('builtins', 'build_inputs')
@builtin.type(HeaderDirectory, in_type=string_types + (HeaderFile,))
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
