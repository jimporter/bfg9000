from six import string_types

from .find import exclude_globs, filter_by_platform
from .hooks import builtin
from ..file_types import *
from ..path import Path, Root


@builtin.globals('build_inputs')
@builtin.type(File)
def generic_file(build, name):
    return build.add_source(File(Path(name, Root.srcdir)))


@builtin.globals('build_inputs')
@builtin.type(SourceFile)
def source_file(build, name, lang=None):
    return build.add_source(SourceFile(Path(name, Root.srcdir), lang))


@builtin.globals('build_inputs')
@builtin.type(HeaderFile)
def header_file(build, name, lang=None):
    return build.add_source(HeaderFile(Path(name, Root.srcdir), lang))


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.


def _find(builtins, name, include, type, exclude, filter):
    if not include:
        return None
    return builtins['find_files'](name, include, type, None, exclude, filter,
                                  as_object=True)


@builtin.globals('builtins', 'build_inputs')
@builtin.type(Directory, in_type=(string_types, File))
def directory(builtins, build, name, include=None, exclude=exclude_globs,
              filter=filter_by_platform):
    if isinstance(name, File):
        path = name.path.parent()
    else:
        path = Path(name, Root.srcdir)

    files = _find(builtins, name, include, '*', exclude, filter)
    return Directory(path, files)


@builtin.globals('builtins', 'build_inputs')
@builtin.type(HeaderDirectory, in_type=(string_types, HeaderFile))
def header_directory(builtins, build, name, include=None,
                     exclude=exclude_globs, filter=filter_by_platform,
                     system=False):
    if isinstance(name, HeaderFile):
        path = name.path.parent()
    else:
        path = Path(name, Root.srcdir)

    files = _find(builtins, name, include, 'f', exclude, filter)
    return HeaderDirectory(path, files, system)
