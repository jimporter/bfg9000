import ntpath
import os.path
import posixpath
import unittest.mock

from .. import *

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


def skip_if_platform(platform, hide=False):
    return skip_pred(lambda x: x.platform_name == platform,
                     'not supported for platform "{}"'.format(platform), hide)


def only_if_platform(platform, hide=False):
    return skip_pred(lambda x: x.platform_name != platform,
                     'only supported for platform "{}"'.format(platform), hide)


class AttrDict:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CrossPlatformTestCase(TestCase):
    _platforms = ['linux', 'winnt', 'macos']

    def __init__(self, *args, clear_variables=False, variables={},
                 platform_name=None, **kwargs):
        self.platform_name = platform_name

        TestCase.__init__(self, *args, **kwargs)
        if self.platform_name is None:
            return

        self.env = make_env(platform=self.platform_name,
                            clear_variables=clear_variables,
                            variables=variables)

    @property
    def Path(self):
        return self.env.host_platform.Path

    def shortDescription(self):
        return self.platform_name

    def parameterize(self):
        return parameterize_tests(self, platform_name=self._platforms)


class PathTestCase(TestCase):
    _path_infos = [
        (Path, os.path, 'native'),
        (PosixPath, posixpath, 'posix'),
        (WindowsPath, ntpath, 'windows'),
    ]

    def __init__(self, *args, path_info=None, **kwargs):

        TestCase.__init__(self, *args, **kwargs)
        if path_info is None:
            return
        self.Path, self.ospath, self._desc = path_info

    def shortDescription(self):
        return self._desc

    def parameterize(self):
        return parameterize_tests(self, path_info=self._path_infos)
