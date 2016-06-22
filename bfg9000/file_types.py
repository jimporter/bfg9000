from six import string_types as _string_types

from .iterutils import listify as _listify
from .languages import src2lang as _src2lang, hdr2lang as _hdr2lang
from .path import InstallRoot as _InstallRoot
from .safe_str import safe_str as _safe_str


def objectify(thing, valid_type, creator, in_type=_string_types, **kwargs):
    if isinstance(thing, valid_type):
        return thing
    elif not isinstance(thing, in_type):
        raise TypeError('expected a {} or a {}'.format(valid_type, in_type))
    else:
        if creator is None:
            creator = valid_type
        # XXX: Come up with a way to provide args to prepend?
        return creator(thing, **kwargs)


class Node(object):
    private = False

    def __init__(self, path):
        self.creator = None
        self.path = path

    def _safe_str(self):
        return _safe_str(self.path)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.path == rhs.path


class Phony(Node):
    pass


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
    def __init__(self, path, files=None, external=False):
        File.__init__(self, path, external)
        self.files = files


class SourceFile(File):
    def __init__(self, path, lang=None, external=False):
        File.__init__(self, path, external)
        self.lang = lang or _src2lang.get(path.ext())


class HeaderFile(File):
    install_kind = 'data'
    install_root = _InstallRoot.includedir

    def __init__(self, path, lang=None, external=False):
        File.__init__(self, path, external)
        self.lang = lang or _hdr2lang.get(path.ext())


class PrecompiledHeader(HeaderFile):
    install_kind = None


class MsvcPrecompiledHeader(PrecompiledHeader):
    def __init__(self, path, object_path, header_name, format, lang,
                 external=False):
        PrecompiledHeader.__init__(self, path, lang, external)
        self.object_file = ObjectFile(object_path, format, self.lang, external)
        self.object_file.private = True
        self.header_name = header_name


class HeaderDirectory(Directory):
    install_kind = 'data'
    install_root = _InstallRoot.includedir

    def __init__(self, path, files=None, system=False, external=False):
        Directory.__init__(self, path, files, external)
        self.system = system


class Binary(File):
    install_kind = 'program'

    def __init__(self, path, format, external=False):
        File.__init__(self, path, external)
        self.format = format


class ObjectFile(Binary):
    def __init__(self, path, format, lang, external=False):
        Binary.__init__(self, path, format, external)
        self.lang = lang


class Executable(Binary):
    install_root = _InstallRoot.bindir


class Library(Binary):
    install_root = _InstallRoot.libdir


class StaticLibrary(Library):
    def __init__(self, path, format, lang, external=False):
        Library.__init__(self, path, format, external)
        self.lang = _listify(lang)


class WholeArchive(StaticLibrary):
    def __init__(self, library, external=False):
        StaticLibrary.__init__(self, library.path, library.format,
                               library.lang, external)
        self.library = library


class SharedLibrary(Library):
    pass


class LinkLibrary(SharedLibrary):
    def __init__(self, path, library, external=False):
        SharedLibrary.__init__(self, path, library.format, external)
        self.runtime_deps = [library]


class VersionedSharedLibrary(SharedLibrary):
    def __init__(self, path, format, soname, linkname, external=False):
        SharedLibrary.__init__(self, path, format, external)
        self.soname = LinkLibrary(soname, self, external)
        self.link = LinkLibrary(linkname, self.soname, external)


class ExportFile(File):
    private = True


class DllLibrary(SharedLibrary):
    install_root = _InstallRoot.bindir
    # XXX: When adding support for .NET, this might need to become an instance
    # variable, since .NET DLLs aren't "private".
    private = True

    def __init__(self, path, format, import_name, export_name=None,
                 external=False):
        SharedLibrary.__init__(self, path, format, external)
        self.import_lib = LinkLibrary(import_name, self, external)
        self.export_file = ExportFile(export_name, external)
