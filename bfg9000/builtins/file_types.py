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


@builtin.globals('build_inputs')
def directory(build, name):
    return build.add_source(Directory(Path(name, Root.srcdir)))


@builtin.globals('build_inputs')
def header_directory(build, name, system=False):
    return build.add_source(HeaderDirectory(Path(name, Root.srcdir), system))
