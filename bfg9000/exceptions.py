from subprocess import CalledProcessError  # noqa: F401


class AbortConfigure(Exception):
    pass


class PackageResolutionError(Exception):
    pass


class VersionError(Exception):
    pass


class PackageVersionError(PackageResolutionError, VersionError):
    pass


class ToolNotFoundError(LookupError):
    pass


class NonGlobError(ValueError):
    pass


class SerializationError(ValueError):
    pass
