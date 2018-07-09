from .core import Platform, platform_name, _get_platform_info


class HostPlatform(Platform):
    pass


def platform_info(name=None):
    if name is None:
        name = platform_name()
    return _get_platform_info(name, 'host')
