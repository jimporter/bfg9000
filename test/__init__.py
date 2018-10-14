import mock

from bfg9000.path import Path
from bfg9000.environment import Environment


def make_env(platform=None, clear_variables=False):
    args = (Path('bfgdir'), None, None, Path('srcdir'), Path('builddir'), {},
            (False, False), None)
    if platform:
        with mock.patch('bfg9000.platforms.host.platform_name',
                        return_value=platform):
            env = Environment(*(args + (platform,)))
    else:
        env = Environment(*args)

    if clear_variables:
        env.variables = {}
    return env
