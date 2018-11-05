import mock
import unittest

from bfg9000.platforms import host, platform_name


class TestHostPlatform(unittest.TestCase):
    def setUp(self):
        platform_name._reset()

    def tearDown(self):
        platform_name._reset()

    def test_default(self):
        with mock.patch('platform.system', return_value='Linux'):
            platform = host.platform_info()
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')

    def test_cygwin(self):
        platform = host.platform_info('cygwin')
        self.assertEqual(platform.name, 'cygwin')
        self.assertEqual(platform.species, 'cygwin')
        self.assertEqual(platform.genus, 'cygwin')
        self.assertEqual(platform.family, 'posix')

    def test_darwin(self):
        platform = host.platform_info('macos')
        self.assertEqual(platform.name, 'macos')
        self.assertEqual(platform.species, 'macos')
        self.assertEqual(platform.genus, 'darwin')
        self.assertEqual(platform.family, 'posix')

        # TODO: remove this after 0.4 is released.
        with mock.patch('warnings.warn'):
            platform = host.platform_info('darwin')
            self.assertEqual(platform.name, 'macos')
            self.assertEqual(platform.species, 'macos')
            self.assertEqual(platform.genus, 'darwin')
            self.assertEqual(platform.family, 'posix')

            self.assertEqual(platform.name, 'darwin')

    def test_linux(self):
        platform = host.platform_info('linux')
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.species, 'linux')
        self.assertEqual(platform.genus, 'linux')
        self.assertEqual(platform.family, 'posix')

    def test_windows(self):
        platform = host.platform_info('winnt')
        self.assertEqual(platform.name, 'winnt')
        self.assertEqual(platform.species, 'winnt')
        self.assertEqual(platform.genus, 'winnt')
        self.assertEqual(platform.family, 'windows')

        # TODO: remove this after 0.4 is released.
        with mock.patch('warnings.warn'):
            platform = host.platform_info('windows')
            self.assertEqual(platform.name, 'winnt')
            self.assertEqual(platform.species, 'winnt')
            self.assertEqual(platform.genus, 'winnt')
            self.assertEqual(platform.family, 'windows')

            self.assertEqual(platform.name, 'windows')

    def test_unknown(self):
        platform = host.platform_info('unknown')
        self.assertEqual(platform.name, 'unknown')
        self.assertEqual(platform.species, 'unknown')
        self.assertEqual(platform.genus, 'unknown')
        self.assertEqual(platform.family, 'posix')
