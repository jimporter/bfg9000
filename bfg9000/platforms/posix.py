from .basepath import BasePath, Root, InstallRoot
from .core import Platform
from .host import HostPlatform
from .target import TargetPlatform


class PosixPath(BasePath):
    _localized_sep = BasePath.sep

    def _localize_path(self, path):
        return path


class PosixPlatform(Platform):
    Path = PosixPath

    @property
    def _triplet_vendor(self):
        if self.genus == 'darwin':
            return 'apple'
        return super()._triplet_vendor

    @property
    def _triplet_sys_abi(self):
        if self.genus == 'darwin':
            return 'darwin'
        elif self.genus == 'linux':
            abi = 'android' if self.species == 'android' else 'gnu'
            return 'linux-' + abi
        elif self.genus == 'cygwin':
            return 'windows-cygnus'
        return self.species

    @property
    def family(self):
        return 'posix'

    @property
    def object_format(self):
        return 'elf'


class PosixHostPlatform(HostPlatform, PosixPlatform):
    @property
    def include_dirs(self):
        return [PosixPath('/usr/local/include/', Root.absolute),
                PosixPath('/usr/include/', Root.absolute)]

    @property
    def lib_dirs(self):
        return [PosixPath('/usr/local/lib/', Root.absolute),
                PosixPath('/lib/', Root.absolute),
                PosixPath('/usr/lib/', Root.absolute)]

    @property
    def has_path_ext(self):
        return False


class PosixTargetPlatform(TargetPlatform, PosixPlatform):
    @property
    def executable_ext(self):
        return ''

    @property
    def shared_library_ext(self):
        return '.so'

    @property
    def has_import_library(self):
        return False

    @property
    def has_versioned_library(self):
        return True

    @property
    def has_frameworks(self):
        return False

    @property
    def install_dirs(self):
        IRoot = InstallRoot
        return {
            IRoot.prefix     : PosixPath('/usr/local/', Root.absolute),
            IRoot.exec_prefix: PosixPath('', IRoot.prefix),
            IRoot.bindir     : PosixPath('bin/', IRoot.exec_prefix),
            IRoot.libdir     : PosixPath('lib/', IRoot.exec_prefix),
            IRoot.includedir : PosixPath('include/', IRoot.prefix),
            IRoot.datadir    : PosixPath('share/', IRoot.prefix),
            IRoot.mandir     : PosixPath('man/', IRoot.datadir),
        }


class DarwinPlatform(PosixPlatform):
    @property
    def object_format(self):
        return 'mach-o'


class DarwinHostPlatform(PosixHostPlatform, DarwinPlatform):
    pass


class DarwinTargetPlatform(PosixTargetPlatform, DarwinPlatform):
    @property
    def shared_library_ext(self):
        return '.dylib'

    @property
    def has_frameworks(self):
        return True
