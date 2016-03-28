from .hooks import builtin
from ..file_types import *
from ..path import Path, Root


@builtin
def source_file(name, lang=None):
    # XXX: Add a way to make a generic File object instead of a SourceFile?
    return SourceFile(Path(name, Root.srcdir), lang)


@builtin
def header(name, lang=None):
    return HeaderFile(Path(name, Root.srcdir), lang)


@builtin
def directory(name):
    return Directory(Path(name, Root.srcdir))


@builtin
def header_directory(name, system=False):
    return HeaderDirectory(Path(name, Root.srcdir), system)
