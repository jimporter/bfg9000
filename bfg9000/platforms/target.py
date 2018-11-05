from .core import Platform, platform_name, _get_platform_info
from ..iterutils import listify


class TargetPlatform(Platform):
    _package_map = {}

    def transform_package(self, name):
        return self._package_map.get(name, name)


def platform_info(name=None):
    if name is None:
        name = platform_name()
    return _get_platform_info(name, 'target')
