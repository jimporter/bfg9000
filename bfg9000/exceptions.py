from subprocess import CalledProcessError


class PackageResolutionError(Exception):
    pass


class VersionError(Exception):
    pass


class PackageVersionError(PackageResolutionError, VersionError):
    pass
