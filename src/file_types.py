import build_inputs
from path import Path

class SourceFile(build_inputs.File):
    def __init__(self, name, source=Path.srcdir, lang=None):
        build_inputs.File.__init__(self, name, source=source)
        self.lang = lang

class HeaderFile(build_inputs.File):
    install_kind = 'data'
    install_root = Path.includedir

class HeaderDirectory(build_inputs.Directory):
    install_root = Path.includedir

class ObjectFile(build_inputs.File):
    def __init__(self, name, source=Path.builddir, lang=None):
        build_inputs.File.__init__(self, name, source)
        self.lang = lang

class Binary(build_inputs.File):
    install_kind = 'program'

class Executable(Binary):
    install_root = Path.bindir

class Library(Binary):
    install_root = Path.libdir

    def __init__(self, lib_name, name, source=Path.builddir):
        Binary.__init__(self, name, source)
        self.lib_name = lib_name

class StaticLibrary(Library):
    pass

class SharedLibrary(Library):
    pass

# Used for Windows DLL files, which aren't linked to directly. Import libraries
# are handled via SharedLibrary above.
class DynamicLibrary(Library):
    pass

class ExternalLibrary(Library):
    def __init__(self, name):
        # TODO: Keep track of the external lib's actual location on the
        # filesystem?
        Library.__init__(self, name, name)
