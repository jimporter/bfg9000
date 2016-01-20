from .hooks import builtin
from ..file_types import *


@builtin
def source_file(name, lang=None):
    # XXX: Add a way to make a generic File object instead of a SourceFile?
    return SourceFile(name, Root.srcdir, lang)


@builtin
def directory(name):
    return Directory(name, Root.srcdir)


@builtin
def header(name):
    return HeaderFile(name, Root.srcdir)


@builtin
def header_directory(name, system=False):
    return HeaderDirectory(name, Root.srcdir, system)
