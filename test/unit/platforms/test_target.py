import mock
import unittest

from bfg9000.platforms import platform_name, target
from bfg9000.platforms.framework import Framework


class TestTargetPlatform(unittest.TestCase):
    def setUp(self):
        platform_name._reset()

    def tearDown(self):
        platform_name._reset()

    def test_default(self):
        with mock.patch('platform.system', return_value='Linux'):
            platform = target.platform_info()
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')

    def test_cygwin(self):
        platform = target.platform_info('cygwin')
        self.assertEqual(platform.name, 'cygwin')
        self.assertEqual(platform.species, 'cygwin')
        self.assertEqual(platform.genus, 'cygwin')
        self.assertEqual(platform.family, 'posix')

        windows = target.platform_info('cygwin')
        posix = target.platform_info('linux')
        for i in ('object_format', 'executable_ext', 'shared_library_ext',
                  'has_import_library', 'has_versioned_library'):
            self.assertEqual(getattr(platform, i), getattr(windows, i))
        for i in ('has_frameworks', 'install_dirs'):
            self.assertEqual(getattr(platform, i), getattr(posix, i))

    def test_darwin(self):
        platform = target.platform_info('macos')
        self.assertEqual(platform.name, 'macos')
        self.assertEqual(platform.species, 'macos')
        self.assertEqual(platform.genus, 'darwin')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.transform_package('gl'),
                         Framework('OpenGL'))

        # TODO: remove this after 0.4 is released.
        with mock.patch('warnings.warn'):
            platform = target.platform_info('darwin')
            self.assertEqual(platform.name, 'macos')
            self.assertEqual(platform.species, 'macos')
            self.assertEqual(platform.genus, 'darwin')
            self.assertEqual(platform.family, 'posix')
            self.assertEqual(platform.transform_package('gl'),
                             Framework('OpenGL'))

            self.assertEqual(platform.name, 'darwin')

    def test_linux(self):
        platform = target.platform_info('linux')
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.transform_package('gl'), 'GL')

    def test_windows(self):
        platform = target.platform_info('winnt')
        self.assertEqual(platform.name, 'winnt')
        self.assertEqual(platform.species, 'winnt')
        self.assertEqual(platform.genus, 'winnt')
        self.assertEqual(platform.family, 'windows')
        self.assertEqual(platform.transform_package('gl'), 'opengl32')

        # TODO: remove this after 0.4 is released.
        with mock.patch('warnings.warn'):
            platform = target.platform_info('windows')
            self.assertEqual(platform.name, 'winnt')
            self.assertEqual(platform.species, 'winnt')
            self.assertEqual(platform.genus, 'winnt')
            self.assertEqual(platform.family, 'windows')
            self.assertEqual(platform.transform_package('gl'), 'opengl32')

            self.assertEqual(platform.name, 'windows')

    def test_unknown(self):
        platform = target.platform_info('unknown')
        self.assertEqual(platform.name, 'unknown')
        self.assertEqual(platform.family, 'posix')
