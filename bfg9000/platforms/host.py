from .core import _get_platform_info, _platform_info, Platform


class HostPlatform(Platform):
    pass


def platform_info(*args, **kwargs):
    return _platform_info('host', *args, **kwargs)


def from_json(value):
    return _get_platform_info('host', value['genus'], value['species'],
                              value['arch'])
