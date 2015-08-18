version_string = '0.1.0-dev'

try:
    import platform
    from packaging.version import Version
    version = Version(version_string)
    python_version = Version(platform.python_version())
except ImportError:
    pass
