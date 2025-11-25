from . import iterutils as _iterutils
from . import path as _path
from . import safe_str as _safe_str


class DefaultHandler(RuntimeError):
    pass


class Cloneable:
    _clone_handlers = {}

    class handler:
        def __init__(self, fn):
            self.fn = fn

        def __set_name__(self, owner, name):
            # Ensure each class setting a handler has its own set of handlers.
            if '_clone_handlers' not in vars(owner):
                owner._clone_handlers = owner._clone_handlers.copy()
            owner._clone_handlers[name] = self.fn

    def __init__(self, *, parent=None):
        self.parent = parent

    @handler
    def parent(old, new, pathfn, recursive, *args):
        if not recursive:
            return None
        raise DefaultHandler()

    def clone(self, pathfn, recursive=False):
        if recursive and self.parent:
            # Clone the parent...
            pclone = self.parent.clone(pathfn, recursive)
            # ... and then find ourself in the parent.
            for k, v in vars(self.parent).items():
                if self is v:
                    return vars(pclone)[k]
            raise TypeError('unable to find self in parent')
        else:
            return self.do_clone(pathfn, recursive)

    def do_clone(self, pathfn, recursive, seen=None):
        def clone_attr(thing, attr_name=None):
            if attr_name and attr_name in self._clone_handlers:
                try:
                    return self._clone_handlers[attr_name](
                        self, clone, pathfn, recursive, seen
                    )
                except DefaultHandler:
                    pass

            if _iterutils.ismapping(thing):
                return type(thing)((clone_attr(k), clone_attr(v))
                                   for k, v in thing.items())
            elif _iterutils.isiterable(thing):
                return type(thing)(clone_attr(i) for i in thing)
            elif isinstance(thing, _path.BasePath):
                return pathfn(thing, self)
            elif recursive and isinstance(thing, Cloneable):
                return thing.do_clone(pathfn, recursive, seen)
            else:
                return thing

        if seen is None:
            seen = {}
        if id(self) in seen:
            return seen[id(self)]

        clone = type(self).__new__(type(self))
        seen[id(self)] = clone
        for k, v in vars(self).items():
            setattr(clone, k, clone_attr(v, attr_name=k))
        return clone


class Node(_safe_str.safe_string_ops):
    def __init__(self, path, *, private=False, **kwargs):
        super().__init__(**kwargs)
        self.creator = None
        self.path = path
        self.private = private

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
        return type(self) is type(rhs) and self.path == rhs.path

    def __ne__(self, rhs):
        return not (self == rhs)


class Phony(Node):
    pass


class BaseFile(Cloneable):
    pass


class FileOrDirectory(Node, BaseFile):
    install_kind = 'data'
    install_root = None

    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)
        self.post_install = None

    @property
    def install_deps(self):
        return []

    @Cloneable.handler
    def creator(old, new, pathfn, *args):
        return None


class File(FileOrDirectory):
    def __init__(self, path, **kwargs):
        if path.directory:
            raise ValueError('expected a non-directory')
        super().__init__(path, **kwargs)

    @property
    def install_suffix(self):
        if self.path.root == _path.Root.srcdir:
            return self.path.basename()
        return self.path.suffix


class Directory(FileOrDirectory):
    def __init__(self, path, files=None, **kwargs):
        super().__init__(path.as_directory(), **kwargs)
        self.files = files

    @property
    def install_suffix(self):
        return ''


class CodeFile(File):
    def __init__(self, path, lang, **kwargs):
        super().__init__(path, **kwargs)
        self.lang = lang


class SourceFile(CodeFile):
    pass


class HeaderFile(CodeFile):
    install_root = _path.InstallRoot.includedir


class PrecompiledHeader(HeaderFile):
    install_root = None


class MsvcPrecompiledHeader(PrecompiledHeader):
    def __init__(self, path, object_path, header_name, format, lang, **kwargs):
        super().__init__(path, lang, **kwargs)
        self.object_file = ObjectFile(object_path, format, self.lang,
                                      parent=self, private=True)
        self.header_name = header_name


class HeaderDirectory(Directory):
    install_root = _path.InstallRoot.includedir

    def __init__(self, path, files=None, system=False, langs=None, **kwargs):
        super().__init__(path, files, **kwargs)
        self.system = system
        self.langs = _iterutils.listify(langs)


class ModuleDefFile(File):
    pass


class ManPage(File):
    install_root = _path.InstallRoot.mandir

    def __init__(self, path, level, **kwargs):
        super().__init__(path, **kwargs)
        self.level = level

    @property
    def install_suffix(self):
        return 'man{}/{}'.format(self.level, self.path.basename())


class Binary(File):
    install_root = _path.InstallRoot.libdir

    def __init__(self, path, format, lang=None, **kwargs):
        super().__init__(path, **kwargs)
        self.format = format
        self.lang = lang


class ObjectFile(Binary):
    pass


# This is used by JVM languages to hold a list of all the object files
# generated by a particular source file's compilation.
class ObjectFileList(ObjectFile):
    install_root = None

    def __init__(self, path, object_name, format, lang=None, **kwargs):
        super().__init__(path, format, lang, **kwargs)
        self.object_file = ObjectFile(object_name, format, lang, parent=self)


# This represents any kind of binary data that's been "linked" (or had some
# similar process applied to it) so that it can be used by a linker/loader,
# installed to the system, etc.
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


class LinkLibrary(SharedLibrary):
    def __init__(self, path, library, **kwargs):
        super().__init__(path, library.format, library.lang, **kwargs)
        self.library = library
        self.linktime_deps = [library]

    @property
    def runtime_file(self):
        return self.library.runtime_file


class LoadLibrary(LinkLibrary):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime_deps = [self.library]

    @property
    def runtime_file(self):
        return self


class VersionedSharedLibrary(SharedLibrary):
    def __init__(self, path, format, lang, soname_path, linkname_path,
                 **kwargs):
        super().__init__(path, format, lang, **kwargs)
        self.soname = LoadLibrary(soname_path, self, parent=self)
        self.link = LinkLibrary(linkname_path, self.soname, parent=self)
        # At runtime, the loader will look for the soname for this library.
        self.runtime_deps = [self.soname]

    @property
    def runtime_file(self):
        return self.soname


class StaticLibrary(Library):
    def __init__(self, path, format, lang=None, forward_opts=None, **kwargs):
        super().__init__(path, format, lang, **kwargs)
        self.forward_opts = forward_opts


class WholeArchive(StaticLibrary):
    def __init__(self, library):
        self.library = library

    def __getattribute__(self, name):
        if name in ['library', '_safe_str', '__repr__', '__hash__', '__eq__']:
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, 'library'), name)


class ExportFile(File):
    def __init__(self, path, *, private=True, **kwargs):
        super().__init__(path, private=private, **kwargs)


# This refers specifically to DLL files that have an import library, not just
# anything with a .dll extension (for instance, .NET DLLs are just regular
# shared libraries). While this is a "library" in some senses, since you can't
# link to it during building, we just consider it a LinkedBinary.
class DllBinary(LinkedBinary):
    install_root = _path.InstallRoot.bindir

    def __init__(self, path, format, lang, import_path, export_path=None, *,
                 private=True, **kwargs):
        super().__init__(path, format, lang, private=private, **kwargs)
        self.import_lib = LinkLibrary(import_path, self, parent=self)
        self.export_file = (ExportFile(export_path, parent=self)
                            if export_path else None)

    @property
    def runtime_file(self):
        return self


class DualUseLibrary(BaseFile):
    def __init__(self, shared, static):
        super().__init__()
        self.shared = shared
        self.static = static
        self.shared.parent = self.static.parent = self

    @property
    def all(self):
        return [self.shared, self.static]

    @Cloneable.handler
    def shared(old, new, pathfn, *args):
        # Always clone the shared library, even when cloning non-recursively.
        shared = old.shared.do_clone(pathfn, *args)
        shared.parent = new
        return shared

    @Cloneable.handler
    def static(old, new, pathfn, *args):
        # Ditto for cloning the static library.
        static = old.static.do_clone(pathfn, *args)
        static.parent = new
        return static

    def __repr__(self):
        return '<DualUseLibrary {!r}>'.format(self.shared.path)

    def __hash__(self):
        return hash(self.shared.path)

    def __eq__(self, rhs):
        return (type(self) is type(rhs) and self.shared == rhs.shared and
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


class PkgConfigPcFile(File):
    install_root = _path.InstallRoot.libdir
