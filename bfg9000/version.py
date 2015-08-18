import platform
from packaging.version import Version

version_string = '0.1.0-dev'
version = Version(version_string)
python_version = Version(platform.python_version())
