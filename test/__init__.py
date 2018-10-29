import mock

from bfg9000.environment import Environment
from bfg9000.path import abspath, Path, Root


def make_env(platform=None, clear_variables=False):
    args = (Path('bfgdir', Root.srcdir), None, None, abspath('srcdir'),
            abspath('builddir'), {}, (False, False))
    if platform:
        with mock.patch('bfg9000.platforms.host.platform_name',
                        return_value=platform), \
             mock.patch('bfg9000.platforms.target.platform_name',
                        return_value=platform):  # noqa
            env = Environment(*args)
    else:
        env = Environment(*args)

    if clear_variables:
        env.variables = {}
    return env
