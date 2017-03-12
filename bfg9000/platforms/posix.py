from . import Platform
from ..file_types import Framework
from ..path import Path, Root, InstallRoot


class PosixPlatform(Platform):
    _package_map = {
        'gl': 'GL',
        'glu': 'GLU',
        'zlib': 'z',
    }

    @property
    def flavor(self):
        return 'posix'

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
    def include_dirs(self):
        return ['/usr/local/include', '/usr/include']

    @property
    def lib_dirs(self):
        return ['/usr/local/lib', '/lib', '/usr/lib']

    @property
    def install_dirs(self):
        return {
            InstallRoot.prefix:      Path('/usr/local', Root.absolute),
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir:      Path('bin', InstallRoot.exec_prefix),
            InstallRoot.libdir:      Path('lib', InstallRoot.exec_prefix),
            InstallRoot.includedir:  Path('include', InstallRoot.prefix),
        }

    @property
    def destdir(self):
        return True


class LinuxPlatform(PosixPlatform):
    @property
    def object_format(self):
        return 'elf'


class DarwinPlatform(PosixPlatform):
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
