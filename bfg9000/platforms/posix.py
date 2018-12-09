from .basepath import BasePath, Root, InstallRoot
from .core import Platform
from .framework import Framework
from .host import HostPlatform
from .target import TargetPlatform


class PosixPath(BasePath):
    def _localize_path(self, path):
        return path


class PosixPlatform(Platform):
    @property
    def _triplet_vendor(self):
        if self.genus == 'darwin':
            return 'apple'
        return Platform._triplet_vendor.fget(self)

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

    Path = PosixPath


class PosixHostPlatform(HostPlatform, PosixPlatform):
    @property
    def include_dirs(self):
        return ['/usr/local/include', '/usr/include']

    @property
    def lib_dirs(self):
        return ['/usr/local/lib', '/lib', '/usr/lib']

    @property
    def destdir(self):
        return True


class PosixTargetPlatform(TargetPlatform, PosixPlatform):
    _package_map = {
        'gl': 'GL',
        'glu': 'GLU',
        'zlib': 'z',
    }

    @property
    def object_format(self):
        return 'elf'

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
        return {
            InstallRoot.prefix     : PosixPath('/usr/local', Root.absolute),
            InstallRoot.exec_prefix: PosixPath('', InstallRoot.prefix),
            InstallRoot.bindir     : PosixPath('bin', InstallRoot.exec_prefix),
            InstallRoot.libdir     : PosixPath('lib', InstallRoot.exec_prefix),
            InstallRoot.includedir : PosixPath('include', InstallRoot.prefix),
        }


class DarwinTargetPlatform(PosixTargetPlatform):
    _package_map = {
        'gl': Framework('OpenGL'),
        'glu': Framework('OpenGL'),
        'glut': Framework('GLUT'),
    }

    @property
    def object_format(self):
        return 'mach-o'

    @property
    def shared_library_ext(self):
        return '.dylib'

    @property
    def has_frameworks(self):
        return True
