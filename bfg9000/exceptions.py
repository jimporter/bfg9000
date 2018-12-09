from subprocess import CalledProcessError  # noqa: F401


class PackageResolutionError(Exception):
    pass


class VersionError(Exception):
    pass


class PackageVersionError(PackageResolutionError, VersionError):
    pass
