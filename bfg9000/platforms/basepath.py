import ntpath
import os
import posixpath
from enum import Enum
from itertools import chain

from .. import safe_str
from ..objutils import objectify

Root = Enum('Root', ['srcdir', 'builddir', 'absolute'])
InstallRoot = Enum('InstallRoot', ['prefix', 'exec_prefix', 'bindir', 'libdir',
                                   'includedir', 'datadir', 'mandir'])
DestDir = Enum('DestDir', ['destdir'])


class BasePath(safe_str.safe_string):
    __slots__ = ['destdir', 'root', 'suffix']

    curdir = posixpath.curdir
    pardir = posixpath.pardir
    sep = posixpath.sep

    __repr_variables = dict(
        [(i, '$({})'.format(i.name)) for i in chain(Root, InstallRoot)] +
        [(DestDir.destdir, '$(DESTDIR)')]
    )

    def __init__(self, path, root=Root.builddir, destdir=None, directory=None):
        if destdir and isinstance(root, Root) and root != Root.absolute:
            raise ValueError('destdir only applies to absolute or install ' +
                             'paths')
        drive, normpath, isdir = self.__normalize(path, expand_user=True)
        if directory is False and isdir:
            raise ValueError('expected a non-directory path')

        if posixpath.isabs(normpath):
            root = Root.absolute
        elif root == Root.absolute:
            raise ValueError("'{}' is not absolute".format(path))
        elif isinstance(root, BasePath):
            normpath, isdir = self.__join(root.suffix, path)
            if destdir is None:
                destdir = root.destdir
            root = root.root

        if not isinstance(root, (Root, InstallRoot)):
            raise ValueError('invalid root {!r}'.format(root))
        if ( normpath == posixpath.pardir or
             normpath.startswith(posixpath.pardir + posixpath.sep) ):
            raise ValueError("too many '..': path cannot escape root")

        self.suffix = drive + normpath
        self.root = root
        self.directory = directory or isdir or normpath == ''
        self.destdir = bool(destdir)

    @classmethod
    def abspath(cls, path, directory=None, absdrive=True):
        drive, path, isdir = cls.__normalize(path, expand_user=True)
        cwddrive, cwdpath, _ = cls.__normalize(os.getcwd())

        if not drive and absdrive:
            drive = cwddrive
        path, _ = cls.__join(cwdpath, path)
        if directory is False and isdir:
            raise ValueError('expected a non-directory path')
        return cls(drive + path, Root.absolute, directory=directory or isdir)

    @classmethod
    def ensure(cls, path, root=Root.builddir, destdir=False, directory=None, *,
               base=None, strict=False):
        result = objectify(path, base or cls, cls, root=root, destdir=destdir,
                           directory=directory)
        raw_root = root.root if isinstance(root, cls) else root
        if strict and result.root != raw_root:
            raise ValueError('expected root of {!r}, but got {!r}'
                             .format(raw_root.name, result.root.name))
        return result

    @staticmethod
    def __normpath(path):
        path = path.replace('\\', '/')
        isdir = posixpath.basename(path) in ('', posixpath.curdir,
                                             posixpath.pardir)
        path = posixpath.normpath(path)
        if path == posixpath.curdir:
            path = ''
        return path, isdir

    @classmethod
    def __normalize(cls, path, expand_user=False):
        if expand_user:
            path = os.path.expanduser(path)
        drive, path = ntpath.splitdrive(path)
        if drive and not ntpath.isabs(path):
            raise ValueError('relative paths with drives not supported')

        drive = drive.replace('\\', '/')
        path, isdir = cls.__normpath(path)
        return drive, path, isdir

    @classmethod
    def __join(cls, path1, path2):
        return cls.__normpath(posixpath.join(path1, path2))

    def __localize(self, thing, localize=True):
        if localize and isinstance(thing, str):
            return self._localize_path(thing)
        return thing

    def cross(self, env):
        cls = env.target_platform.Path
        return cls(self.suffix, self.root, False, self.directory)

    def as_directory(self):
        if self.directory:
            return self
        return type(self)(self.suffix, self.root, self.destdir, True)

    def has_drive(self):
        return (self.root == Root.absolute and
                ntpath.splitdrive(self.suffix)[0] != '')

    def parent(self):
        if not self.suffix:
            raise ValueError('already at root')
        return type(self)(posixpath.dirname(self.suffix), self.root,
                          self.destdir, directory=True)

    def append(self, path):
        drive, path, isdir = self.__normalize(path, expand_user=True)
        if not posixpath.isabs(path):
            path, _ = self.__join(self.suffix, path or '.')
        return type(self)(drive + path, self.root, self.destdir, isdir)

    def ext(self):
        return posixpath.splitext(self.suffix)[1]

    def addext(self, ext):
        return type(self)(self.suffix + ext, self.root, self.destdir,
                          self.directory)

    def stripext(self, replace=None):
        name = posixpath.splitext(self.suffix)[0]
        if replace:
            name += replace
        return type(self)(name, self.root, self.destdir, self.directory)

    def splitleaf(self):
        return self.parent(), self.basename()

    def split(self):
        # This is guaranteed to work since `suffix` is normalized.
        return self.suffix.split(posixpath.sep) if self.suffix else []

    def basename(self):
        return posixpath.basename(self.suffix)

    def relpath(self, start, prefix='', localize=True):
        if self.root == Root.absolute:
            return self.__localize(self.suffix, localize)
        if self.root != start.root:
            raise ValueError('source mismatch')

        rel = posixpath.relpath(self.suffix or posixpath.curdir,
                                start.suffix or posixpath.curdir)
        if prefix and rel == posixpath.curdir:
            return prefix
        result = posixpath.join(prefix, rel)
        return self.__localize(result, localize)

    def reroot(self, root=Root.builddir):
        return type(self)(self.suffix, root, self.destdir, self.directory)

    def to_json(self):
        suffix = self.suffix
        if self.directory and not suffix.endswith(posixpath.sep):
            if suffix:
                suffix += posixpath.sep
            else:
                suffix = posixpath.curdir + posixpath.sep
        return [suffix, self.root.name, self.destdir]

    @classmethod
    def from_json(cls, data):
        try:
            base = Root[data[1]]
        except KeyError:
            base = InstallRoot[data[1]]
        return cls(data[0], base, data[2])

    def realize(self, variables, executable=False, variable_sep=True,
                localize=True):
        if self.root == Root.absolute:
            variable_sep = False
            root = None
        else:
            root = variables[self.root]

        if executable and root is None and posixpath.sep not in self.suffix:
            root = posixpath.curdir

        # Not all platforms (e.g. Windows) support $(DESTDIR), so only emit the
        # destdir variable if it's defined.
        if self.destdir and DestDir.destdir in variables:
            destdir = variables[DestDir.destdir]
            root = destdir if root is None else destdir + root
        if root is None:
            return self.__localize(self.suffix or posixpath.curdir, localize)
        if not self.suffix:
            return self.__localize(root, localize)

        # Join the separator and the suffix first so that we don't end up with
        # unnecessarily-escaped backslashes on Windows. (It doesn't hurt
        # anything; it just looks weird.)
        suffix = (posixpath.sep + self.suffix if variable_sep else
                  self.suffix)
        return (self.__localize(root, localize) +
                self.__localize(suffix, localize))

    def string(self, variables=None):
        path = self
        result = ''

        while True:
            real = path.realize(variables)
            if isinstance(real, safe_str.jbos):
                path, suffix = real.bits
                result = suffix + result
            elif isinstance(real, BasePath):
                path = real
            else:
                result = real + result
                break

        return result

    def __repr__(self):
        s = self.realize(self.__repr_variables)
        if self.directory and not s.endswith(self._localized_sep):
            s += self._localized_sep
        return '`{}`'.format(s)

    def __hash__(self):
        return hash(self.suffix)

    def __eq__(self, rhs):
        if type(self) is not type(rhs):
            return NotImplemented
        return (self.root == rhs.root and self.suffix == rhs.suffix and
                self.destdir == rhs.destdir)

    def __ne__(self, rhs):
        return not (self == rhs)
