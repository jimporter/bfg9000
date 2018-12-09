from .core import _get_platform_info, _platform_info, Platform


class TargetPlatform(Platform):
    _package_map = {}

    def transform_package(self, name):
        return self._package_map.get(name, name)


def platform_info(*args, **kwargs):
    return _platform_info('target', *args, **kwargs)


def from_json(value):
    return _get_platform_info('target', value['genus'], value['species'],
                              value['arch'])
