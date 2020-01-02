from unittest import mock

from .. import *

from bfg9000.platforms import platform_name, target, posix
from bfg9000.platforms.framework import Framework


class TestTargetPlatform(TestCase):
    def setUp(self):
        platform_name._reset()

    def tearDown(self):
        platform_name._reset()

    def test_default(self):
        with mock.patch('platform.system', return_value='Linux'), \
             mock.patch('platform.machine', return_value='i686'):  # noqa
            platform = target.platform_info()
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'i686-pc-linux-gnu')

    def test_cygwin(self):
        with mock.patch('platform.machine', return_value='x86_64'):
            platform = target.platform_info('cygwin')
        self.assertEqual(platform.name, 'cygwin')
        self.assertEqual(platform.species, 'cygwin')
        self.assertEqual(platform.genus, 'cygwin')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'x86_64-unknown-windows-cygnus')

        windows = target.platform_info('cygwin')
        posix = target.platform_info('linux')
        for i in ('object_format', 'executable_ext', 'shared_library_ext',
                  'has_import_library', 'has_versioned_library'):
            self.assertEqual(getattr(platform, i), getattr(windows, i))
        for i in ('has_frameworks', 'install_dirs'):
            self.assertEqual(getattr(platform, i), getattr(posix, i))

    def test_darwin(self):
        with mock.patch('platform.machine', return_value='x86_64'):
            platform = target.platform_info('macos')
        self.assertEqual(platform.name, 'macos')
        self.assertEqual(platform.species, 'macos')
        self.assertEqual(platform.genus, 'darwin')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'x86_64-apple-darwin')
        self.assertEqual(platform.transform_package('gl'),
                         Framework('OpenGL'))

    def test_linux(self):
        with mock.patch('platform.machine', return_value='x86_64'):
            platform = target.platform_info('linux')
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'x86_64-unknown-linux-gnu')
        self.assertEqual(platform.transform_package('gl'), 'GL')

    def test_android(self):
        with mock.patch('platform.machine', return_value='arm'):
            platform = target.platform_info('android')
        self.assertEqual(platform.name, 'android')
        self.assertEqual(platform.species, 'android')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'arm-unknown-linux-android')
        self.assertEqual(platform.transform_package('gl'), 'GL')

    def test_windows(self):
        with mock.patch('platform.machine', return_value='x86_64'):
            platform = target.platform_info('winnt')
        self.assertEqual(platform.name, 'winnt')
        self.assertEqual(platform.species, 'winnt')
        self.assertEqual(platform.genus, 'winnt')
        self.assertEqual(platform.family, 'windows')
        self.assertEqual(platform.triplet, 'x86_64-unknown-win32')
        self.assertEqual(platform.transform_package('gl'), 'opengl32')

    def test_unknown(self):
        with mock.patch('platform.machine', return_value='x86_64'):
            platform = target.platform_info('onosendai')
        self.assertEqual(platform.name, 'onosendai')
        self.assertEqual(platform.species, 'onosendai')
        self.assertEqual(platform.genus, 'onosendai')
        self.assertEqual(platform.family, 'posix')
        self.assertEqual(platform.triplet, 'x86_64-unknown-onosendai')

    def test_equality(self):
        a = posix.PosixTargetPlatform('linux', 'linux', 'x86_64')
        b = posix.PosixTargetPlatform('linux', 'linux', 'x86_64')
        c = posix.PosixTargetPlatform('linux', 'android', 'arm')

        self.assertTrue(a == b)
        self.assertFalse(a != b)
        self.assertFalse(a == c)
        self.assertTrue(a != c)

    def test_json(self):
        plat = posix.PosixTargetPlatform('linux', 'linux', 'x86_64')
        json = plat.to_json()
        self.assertEqual(target.from_json(json), plat)
