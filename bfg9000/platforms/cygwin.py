from .posix import PosixPlatform, PosixHostPlatform, PosixTargetPlatform


class CygwinPlatform(PosixPlatform):
    @property
    def object_format(self):
        return 'coff'


class CygwinHostPlatform(PosixHostPlatform, CygwinPlatform):
    @property
    def has_path_ext(self):
        return True


class CygwinTargetPlatform(PosixTargetPlatform, CygwinPlatform):
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
