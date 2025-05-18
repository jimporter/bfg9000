import ntpath
import os.path
import posixpath
import unittest.mock

from .. import *
from ..parameterize import ParameterizedTestCase

from bfg9000.path import Path
from bfg9000.platforms.posix import PosixPath
from bfg9000.platforms.windows import WindowsPath


# Fix the mock lib's mock_open function to work with iter(); note: this is
# already fixed in Python 3.7.1.
def mock_open(*args, **kwargs):
    mo = unittest.mock.mock_open(*args, **kwargs)
    handle = mo.return_value
    handle.__iter__.side_effect = lambda: iter(handle.readlines.side_effect())
    return mo


def skip_if_platform(platform):
    return skip_pred(lambda x: x.platform_name == platform,
                     'not supported for platform "{}"'.format(platform))


def only_if_platform(platform):
    return skip_pred(lambda x: x.platform_name != platform,
                     'only supported for platform "{}"'.format(platform))


class AttrDict:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CrossPlatformTestCase(ParameterizedTestCase,
                            params=['linux', 'winnt', 'macos'],
                            dest='platform_name'):
    def __init__(self, *args, clear_variables=False, variables={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = make_env(platform=self.platform_name,
                            clear_variables=clear_variables,
                            variables=variables)

    @property
    def Path(self):
        return self.env.host_platform.Path


class PathTestCase(ParameterizedTestCase,
                   params={
                       'native': (Path, os.path),
                       'posix': (PosixPath, posixpath),
                       'windows': (WindowsPath, ntpath),
                   }, dest=('Path', 'ospath')):
    pass
