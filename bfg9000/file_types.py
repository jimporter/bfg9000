from . import path as _path, safe_str as _safe_str
from .iterutils import listify as _listify


def _clone_traits(exclude=set(), subfiles={}):
    def inner(cls):
        cls._clone_exclude = cls._clone_exclude | exclude
        if subfiles:
            cls._clone_subfiles = cls._clone_subfiles.copy()
            cls._clone_subfiles.update(subfiles)
        return cls

    return inner


class Node(_safe_str.safe_string_ops):
    private = False

    def __init__(self, path):
        self.creator = None
        self.path = path

    def _safe_str(self):
        return _safe_str.safe_str(self.path)

    @property
    def all(self):
        return [self]

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.path == rhs.path

    def __ne__(self, rhs):
        return not (self == rhs)


class Phony(Node):
    pass


class BaseFile:
    pass


class FileOrDirectory(Node, BaseFile):
    _clone_exclude = {'path', 'creator', 'post_install'}
    _clone_subfiles = {}

    install_kind = 'data'
    install_root = None

    def __init__(self, path):
        super().__init__(path)
        self.post_install = None

    @property
    def install_deps(self):
        return []

    def _clone_args(self, pathfn, recursive):
        args = {'path': pathfn(self)}
        for k, v in self.__dict__.items():
            if k in self._clone_exclude:
                continue
            try:
                dest = self._clone_subfiles[k]
                orig = getattr(self, k)
                if orig is None:
                    args[dest] = None
                elif recursive:
                    args[dest] = pathfn(orig)
                else:
                    args[dest] = orig.path
            except KeyError:
                args[k] = v
        return args

    def clone(self, pathfn, recursive=False, inner=None):
        clone = type(self)(**self._clone_args(pathfn, recursive))
        if inner and inner is not self:
            for i in self._clone_subfiles:
                if getattr(self, i) is inner:
                    return getattr(clone, i)
            raise RuntimeError('unable to find inner clone object')
        return clone


class File(FileOrDirectory):
    def __init__(self, path):
        if path.directory:
            raise ValueError('expected a non-directory')
        super().__init__(path)

    @property
    def install_suffix(self):
        if self.path.root == _path.Root.srcdir:
            return self.path.basename()
        return self.path.suffix


@_clone_traits(exclude={'files'})
class Directory(FileOrDirectory):
    def __init__(self, path, files=None):
        super().__init__(path.as_directory())
        self.files = files

    @property
    def install_suffix(self):
        return ''

    def _clone_args(self, pathfn, recursive):
        args = super()._clone_args(pathfn, recursive)
        if self.files is None:
            args['files'] = None
        elif recursive:
            args['files'] = [i.clone(pathfn, recursive) for i in self.files]
        else:
            args['files'] = [i for i in self.files]
        return args


class CodeFile(File):
    def __init__(self, path, lang):
        super().__init__(path)
        self.lang = lang


class SourceFile(CodeFile):
    pass


class HeaderFile(CodeFile):
    install_root = _path.InstallRoot.includedir


class PrecompiledHeader(HeaderFile):
    install_root = None


@_clone_traits(subfiles={'object_file': 'object_path'})
class MsvcPrecompiledHeader(PrecompiledHeader):
    def __init__(self, path, object_path, header_name, format, lang):
        super().__init__(path, lang)
        self.object_file = ObjectFile(object_path, format, self.lang)
        self.object_file.private = True
        self.header_name = header_name

    def _clone_args(self, pathfn, recursive):
        args = super()._clone_args(pathfn, recursive)
        args['format'] = self.object_file.format
        return args


class HeaderDirectory(Directory):
    install_root = _path.InstallRoot.includedir

    def __init__(self, path, files=None, system=False, langs=None):
        super().__init__(path, files)
        self.system = system
        self.langs = _listify(langs)


class ModuleDefFile(File):
    pass


class ManPage(File):
    install_root = _path.InstallRoot.mandir

    def __init__(self, path, level):
        super().__init__(path)
        self.level = level

    @property
    def install_suffix(self):
        return 'man{}/{}'.format(self.level, self.path.basename())


class Binary(File):
    install_root = _path.InstallRoot.libdir

    def __init__(self, path, format, lang=None):
        super().__init__(path)
        self.format = format
        self.lang = lang


class ObjectFile(Binary):
    pass


# This is used by JVM languages to hold a list of all the object files
# generated by a particular source file's compilation.
class ObjectFileList(ObjectFile):
    install_root = None

    def __init__(self, path, object_name, format, lang=None):
        super().__init__(path, format, lang)
        self.object_file = ObjectFile(object_name, format, lang)


# This represents any kind of binary data that's been "linked" (or had some
# similar process applied to it) so that it can be used by a linker/loader,
# installed to the system, etc.
@_clone_traits(exclude={'runtime_deps', 'linktime_deps', 'package_deps'})
class LinkedBinary(Binary):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime_deps = []
        self.linktime_deps = []
        self.package_deps = []

    @property
    def install_deps(self):
        return self.runtime_deps + self.linktime_deps


class Executable(LinkedBinary):
    install_kind = 'program'
    install_root = _path.InstallRoot.bindir


@_clone_traits(exclude={'parent'})
class Library(LinkedBinary):
    @property
    def runtime_file(self):
        return None


# This is used for JVM binaries, which can be both executables and libraries.
# Multiple inheritance is a sign that we should perhaps switch to a trait-based
# system though...
class ExecutableLibrary(Executable, Library):
    install_kind = 'program'
    install_root = _path.InstallRoot.libdir


class SharedLibrary(Library):
    install_kind = 'program'

    @property
    def runtime_file(self):
        return self


@_clone_traits(exclude={'format', 'lang'})
class LinkLibrary(SharedLibrary):
    def __init__(self, path, library):
        super().__init__(path, library.format, library.lang)
        self.library = library
        self.linktime_deps = [library]

    @property
    def runtime_file(self):
        return self.library

    def clone(self, path, recursive=False, inner=None):
        if recursive:
            return self.library.clone(path, True, inner or self)
        return super().clone(path, False, inner)


@_clone_traits(subfiles={'soname': 'soname_path', 'link': 'linkname_path'})
class VersionedSharedLibrary(SharedLibrary):
    def __init__(self, path, format, lang, soname_path, linkname_path):
        super().__init__(path, format, lang)
        self.soname = LinkLibrary(soname_path, self)
        self.link = LinkLibrary(linkname_path, self.soname)


class StaticLibrary(Library):
    def __init__(self, path, format, lang=None, forward_opts=None):
        super().__init__(path, format, lang)
        self.forward_opts = forward_opts


class WholeArchive(StaticLibrary):
    def __init__(self, library):
        self.library = library

    def __getattribute__(self, name):
        if name in ['library', '_safe_str', '__repr__', '__hash__', '__eq__']:
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, 'library'), name)


class ExportFile(File):
    private = True


# This refers specifically to DLL files that have an import library, not just
# anything with a .dll extension (for instance, .NET DLLs are just regular
# shared libraries). While this is a "library" in some senses, since you can't
# link to it during building, we just consider it a LinkedBinary.
@_clone_traits(subfiles={'import_lib': 'import_path',
                         'export_file': 'export_path'})
class DllBinary(LinkedBinary):
    install_root = _path.InstallRoot.bindir
    private = True

    def __init__(self, path, format, lang, import_path, export_path=None):
        super().__init__(path, format, lang)
        self.import_lib = LinkLibrary(import_path, self)
        self.export_file = ExportFile(export_path) if export_path else None


class DualUseLibrary(BaseFile):
    def __init__(self, shared, static):
        self.shared = shared
        self.static = static
        self.shared.parent = self
        self.static.parent = self

    @property
    def all(self):
        return [self.shared, self.static]

    def __repr__(self):
        return '<DualUseLibrary {!r}>'.format(self.shared.path)

    def __hash__(self):
        return hash(self.shared.path)

    def __eq__(self, rhs):
        return (type(self) == type(rhs) and self.shared == rhs.shared and
                self.static == rhs.static)

    def __ne__(self, rhs):
        return not (self == rhs)

    @property
    def package_deps(self):
        return self.shared.package_deps

    @property
    def install_deps(self):
        return self.shared.install_deps

    @property
    def forward_opts(self):
        return self.static.forward_opts

    def clone(self, *args, **kwargs):
        return DualUseLibrary(self.shared.clone(*args, **kwargs),
                              self.static.clone(*args, **kwargs))


class PkgConfigPcFile(File):
    install_root = _path.InstallRoot.libdir
