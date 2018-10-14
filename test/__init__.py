import mock

from bfg9000.environment import Environment


def make_env(platform=None, clear_variables=False):
    if platform:
        with mock.patch('bfg9000.platforms.host.platform_name',
                        return_value=platform):
            env = Environment(None, None, None, None, None, {},
                              (False, False), None, platform)
    else:
        env = Environment(None, None, None, None, None, {},
                          (False, False), None)

    if clear_variables:
        env.variables = {}
    return env
