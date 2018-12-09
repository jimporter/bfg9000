from .basepath import BasePath, InstallRoot
from .core import Platform
from .host import HostPlatform
from .target import TargetPlatform


class WindowsPath(BasePath):
    def _localize_path(self, path):
        return path.replace('/', '\\')


class WindowsPlatform(Platform):
    @property
    def _triplet_sys_abi(self):
        return 'win32'

    @property
    def family(self):
        return 'windows'

    Path = WindowsPath


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
            InstallRoot.prefix     : None,
            InstallRoot.exec_prefix: WindowsPath('', InstallRoot.prefix),
            InstallRoot.bindir     : WindowsPath('', InstallRoot.exec_prefix),
            InstallRoot.libdir     : WindowsPath('', InstallRoot.exec_prefix),
            InstallRoot.includedir : WindowsPath('', InstallRoot.prefix),
        }
