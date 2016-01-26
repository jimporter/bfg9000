import os.path
from six import string_types

from .languages import ext2lang
from .path import InstallRoot, Path, Root
from .safe_str import safe_str


class Node(object):
    def __init__(self, path):
        self.creator = None
        self.path = path

    @property
    def all(self):
        return [self]

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


def objectify(thing, valid_type, creator, *args, **kwargs):
    if isinstance(thing, valid_type):
        return thing
    elif not isinstance(thing, string_types):
        raise TypeError('expected a {} or a string'.format(valid_type))
    else:
        if creator is None:
            creator = valid_type
        # XXX: Come up with a way to provide args to prepend?
        return creator(thing, *args, **kwargs)


def sourcify(thing, valid_type, make_type=None, **kwargs):
    return objectify(thing, valid_type, make_type, root=Root.srcdir, **kwargs)


class File(Node):
    install_kind = None
    install_root = None

    def __init__(self, name, root):
        Node.__init__(self, Path(name, root))
        self.post_install = None


class Directory(File):
    pass


class Phony(Node):
    def __init__(self, name):
        Node.__init__(self, name)


class SourceFile(File):
    def __init__(self, name, root, lang=None):
        File.__init__(self, name, root)
        if lang is None:
            lang = ext2lang.get(os.path.splitext(name)[1])
        self.lang = lang


class HeaderFile(File):
    install_kind = 'data'
    install_root = InstallRoot.includedir


class HeaderDirectory(Directory):
    install_root = InstallRoot.includedir

    def __init__(self, name, root, system=False):
        Directory.__init__(self, name, root)
        self.system = system


class ObjectFile(File):
    def __init__(self, name, root, lang):
        File.__init__(self, name, root)
        self.lang = lang


class Binary(File):
    install_kind = 'program'

    def __init__(self, name, root, lang=None):
        File.__init__(self, name, root)
        self.lang = lang


class Executable(Binary):
    install_root = InstallRoot.bindir


class SystemExecutable(Executable):
    install_root = None


class Library(Binary):
    install_root = InstallRoot.libdir

    @property
    def link(self):
        return self


class StaticLibrary(Library):
    pass


class WholeArchive(StaticLibrary):
    def __init__(self, lib):
        Node.__init__(self, lib.path)
        self.lib = lib
        self.creator = lib.creator
        self.post_install = None

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
