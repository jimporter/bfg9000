import mock
import unittest

from bfg9000.frameworks import Framework
from bfg9000.platforms import platform_name, target


class TestTargetPlatform(unittest.TestCase):
    def setUp(self):
        platform_name._reset()

    def tearDown(self):
        platform_name._reset()

    def test_default(self):
        with mock.patch('platform.system', lambda: 'Linux'):
            platform = target.platform_info()
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.flavor, 'posix')

    def test_cygwin(self):
        platform = target.platform_info('cygwin')
        self.assertEqual(platform.name, 'cygwin')
        self.assertEqual(platform.flavor, 'posix')

        windows = target.platform_info('cygwin')
        posix = target.platform_info('linux')
        for i in ('object_format', 'executable_ext', 'shared_library_ext',
                  'has_import_library', 'has_versioned_library'):
            self.assertEqual(getattr(platform, i), getattr(windows, i))
        for i in ('has_frameworks', 'install_dirs'):
            self.assertEqual(getattr(platform, i), getattr(posix, i))

    def test_darwin(self):
        platform = target.platform_info('darwin')
        self.assertEqual(platform.name, 'darwin')
        self.assertEqual(platform.flavor, 'posix')
        self.assertEqual(platform.transform_package('gl'),
                         Framework('OpenGL'))

    def test_linux(self):
        platform = target.platform_info('linux')
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.flavor, 'posix')
        self.assertEqual(platform.transform_package('gl'), 'GL')

    def test_windows(self):
        platform = target.platform_info('windows')
        self.assertEqual(platform.name, 'windows')
        self.assertEqual(platform.flavor, 'windows')
        self.assertEqual(platform.transform_package('gl'), 'opengl32')

    def test_unknown(self):
        platform = target.platform_info('unknown')
        self.assertEqual(platform.name, 'unknown')
        self.assertEqual(platform.flavor, 'posix')
