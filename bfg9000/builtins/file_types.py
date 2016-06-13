from .find import exclude_globs, filter_by_platform
from .hooks import builtin
from ..file_types import *
from ..path import Path, Root


@builtin.globals('build_inputs')
def generic_file(build, name):
    return build.add_source(File(Path(name, Root.srcdir)))


@builtin.globals('build_inputs')
def source_file(build, name, lang=None):
    return build.add_source(SourceFile(Path(name, Root.srcdir), lang))


@builtin.globals('build_inputs')
def header(build, name, lang=None):
    return build.add_source(HeaderFile(Path(name, Root.srcdir), lang))


# These builtins will find all the files in a directory so that they can be
# added to the distribution. XXX: Perhaps these could be reworked so that
# adding/removing files in directories doesn't force bfg to regenerate build
# files.

@builtin.globals('builtins', 'build_inputs')
def directory(builtins, build, name, include='*', exclude=exclude_globs,
              filter=filter_by_platform):
    builtins['find_files'](name, include, '*', None, exclude, filter)
    return Directory(Path(name, Root.srcdir))


@builtin.globals('builtins', 'build_inputs')
def header_directory(builtins, build, name, include='*', exclude=exclude_globs,
                     filter=filter_by_platform, system=False):
    builtins['find_files'](name, include, 'f', None, exclude, filter)
    return HeaderDirectory(Path(name, Root.srcdir), system)
