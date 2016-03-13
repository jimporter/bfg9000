from six import string_types

from .iterutils import listify
from .languages import ext2lang
from .path import InstallRoot, Path, Root
from .safe_str import safe_str


class Node(object):
    def __init__(self, path):
        self.creator = None
        self.path = path

    def _safe_str(self):
        return safe_str(self.path)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.path == rhs.path


def objectify(thing, valid_type, creator, in_type=string_types, *args,
              **kwargs):
    if isinstance(thing, valid_type):
        return thing
    elif not isinstance(thing, in_type):
        raise TypeError('expected a {} or a {}'.format(valid_type, in_type))
    else:
        if creator is None:
            creator = valid_type
        # XXX: Come up with a way to provide args to prepend?
        return creator(thing, *args, **kwargs)


def sourcify(thing, valid_type, make_type=None, root=Root.srcdir, **kwargs):
    if isinstance(thing, string_types):
        thing = Path(thing, root)
    return objectify(thing, valid_type, make_type, Path, **kwargs)


class File(Node):
    install_kind = None
    install_root = None

    def __init__(self, path, external=False):
        Node.__init__(self, path)
        self.external = external
        self.post_install = None
        self.install_deps = []
        self.runtime_deps = []


class Directory(File):
    pass


class Phony(Node):
    pass


class SourceFile(File):
    def __init__(self, path, lang, external=False):
        File.__init__(self, path, external)
        if lang is None:
            lang = ext2lang.get(path.ext())
        self.lang = lang


class HeaderFile(File):
    install_kind = 'data'
    install_root = InstallRoot.includedir


class HeaderDirectory(Directory):
    install_kind = 'data'
    install_root = InstallRoot.includedir

    def __init__(self, path, system, external=False):
        Directory.__init__(self, path, external)
        self.system = system


class Binary(File):
    install_kind = 'program'


class ObjectFile(Binary):
    def __init__(self, path, lang, external=False):
        Binary.__init__(self, path, external)
        self.lang = lang


class Executable(Binary):
    install_root = InstallRoot.bindir


class Library(Binary):
    install_root = InstallRoot.libdir


class StaticLibrary(Library):
    def __init__(self, path, lang, external=False):
        Library.__init__(self, path, external)
        self.lang = listify(lang)


class WholeArchive(StaticLibrary):
    def __init__(self, lib, external=False):
        StaticLibrary.__init__(self, lib.path, lib.lang, external)
        self.lib = lib


class SharedLibrary(Library):
    pass


class LinkLibrary(SharedLibrary):
    def __init__(self, path, library, external=False):
        SharedLibrary.__init__(self, path, external)
        self.runtime_deps = [library]


class VersionedSharedLibrary(SharedLibrary):
    def __init__(self, path, soname, linkname, external=False):
        SharedLibrary.__init__(self, path, external)
        self.soname = LinkLibrary(soname, self, external)
        self.link = LinkLibrary(linkname, self.soname, external)


class ExportFile(File):
    private = True


class DllLibrary(SharedLibrary):
    install_root = InstallRoot.bindir
    # XXX: When adding support for .NET, this might need to become an instance
    # variable, since .NET DLLs aren't "private".
    private = True

    def __init__(self, path, import_name, export_name=None, external=False):
        SharedLibrary.__init__(self, path, external)
        self.import_lib = LinkLibrary(import_name, self, external)
        self.export_file = ExportFile(export_name, external)
