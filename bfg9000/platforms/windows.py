from . import Platform
from ..path import Path, Root, InstallRoot


class WindowsPlatform(Platform):
    _package_map = {
        'gl': 'opengl32',
        'glu': 'glu32',
        'glut': 'glut32',
    }

    @property
    def flavor(self):
        return 'windows'

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
    def install_dirs(self):
        return {
            InstallRoot.prefix:      None,
            InstallRoot.exec_prefix: Path('', InstallRoot.prefix),
            InstallRoot.bindir:      Path('', InstallRoot.exec_prefix),
            InstallRoot.libdir:      Path('', InstallRoot.exec_prefix),
            InstallRoot.includedir:  Path('', InstallRoot.prefix),
        }

    @property
    def destdir(self):
        return False


class CygwinPlatform(WindowsPlatform):
    @property
    def flavor(self):
        return 'posix'

    @property
    def destdir(self):
        return True
