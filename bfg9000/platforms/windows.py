from .core import Platform
from .host import HostPlatform
from .target import TargetPlatform
from ..path import Path, Root, InstallRoot


class WindowsPlatform(Platform):
    @property
    def flavor(self):
        return 'windows'


class WindowsHostPlatform(HostPlatform, WindowsPlatform):
    @property
    def include_dirs(self):
        # Windows doesn't have standard include dirs; for MSVC, this will get
        # pulled in from the $INCLUDE environment variable.
        return []

    @property
    def lib_dirs(self):
        # Windows doesn't have standard library dirs; for MSVC, this will get
        # pulled in from the $LIB environment variable.
        return []

    @property
    def destdir(self):
        return False


class WindowsTargetPlatform(TargetPlatform, WindowsPlatform):
    _package_map = {
        'gl': 'opengl32',
        'glu': 'glu32',
        'glut': 'glut32',
    }

    @property
    def object_format(self):
        return 'coff'

    @property
    def executable_ext(self):
        return '.exe'

    @property
    def shared_library_ext(self):
        return '.dll'

    @property
    def has_import_library(self):
        return True

    @property
    def has_versioned_library(self):
        return False

    @property
    def has_frameworks(self):
        return False

    @property
    def install_dirs(self):
        return {
            InstallRoot.prefix:      None,
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir:      Path('', InstallRoot.exec_prefix),
            InstallRoot.libdir:      Path('', InstallRoot.exec_prefix),
            InstallRoot.includedir:  Path('', InstallRoot.prefix),
        }
