from .posix import PosixHostPlatform, PosixTargetPlatform


class CygwinHostPlatform(PosixHostPlatform):
    pass


class CygwinTargetPlatform(PosixTargetPlatform):
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
