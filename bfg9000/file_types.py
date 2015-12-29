import os.path

from . import build_inputs
from .languages import ext2lang
from .path import InstallRoot

class SourceFile(build_inputs.File):
    def __init__(self, name, root, lang=None):
        build_inputs.File.__init__(self, name, root)
        if lang is None:
            lang = ext2lang.get( os.path.splitext(name)[1] )
        self.lang = lang

class HeaderFile(build_inputs.File):
    install_kind = 'data'
    install_root = InstallRoot.includedir

class HeaderDirectory(build_inputs.Directory):
    install_root = InstallRoot.includedir

    def __init__(self, name, root, system=False):
        build_inputs.File.__init__(self, name, root)
        self.system = system

class ObjectFile(build_inputs.File):
    def __init__(self, name, root, lang):
        build_inputs.File.__init__(self, name, root)
        self.lang = lang

class Binary(build_inputs.File):
    install_kind = 'program'

    def __init__(self, name, root, lang=None):
        build_inputs.File.__init__(self, name, root)
        self.lang = lang

class Executable(Binary):
    install_root = InstallRoot.bindir

class Library(Binary):
    install_root = InstallRoot.libdir

    @property
    def link(self):
        return self

class StaticLibrary(Library):
    pass

class WholeArchive(StaticLibrary):
    def __init__(self, lib):
        build_inputs.Node.__init__(self)
        self.lib = lib
        self.creator = lib.creator
        self.post_install = None

    @property
    def path(self):
        return self.lib.path

    @property
    def lang(self):
        return self.lib.lang

class SharedLibrary(Library):
    pass

class ImportLibrary(SharedLibrary):
    pass

class DllLibrary(SharedLibrary):
    install_root = InstallRoot.bindir

    def __init__(self, name, import_name, root, lang):
        SharedLibrary.__init__(self, name, root, lang)
        self.import_lib = ImportLibrary(import_name, root, lang)

    @property
    def all(self):
        return [self, self.import_lib]

    @property
    def link(self):
        return self.import_lib

