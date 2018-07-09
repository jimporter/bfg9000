import mock
import unittest

from bfg9000.platforms import host, platform_name


class TestHostPlatform(unittest.TestCase):
    def setUp(self):
        platform_name._reset()

    def tearDown(self):
        platform_name._reset()

    def test_default(self):
        with mock.patch('platform.system', lambda: 'Linux'):
            platform = host.platform_info()
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.flavor, 'posix')

    def test_cygwin(self):
        platform = host.platform_info('cygwin')
        self.assertEqual(platform.name, 'cygwin')
        self.assertEqual(platform.flavor, 'posix')

    def test_darwin(self):
        platform = host.platform_info('darwin')
        self.assertEqual(platform.name, 'darwin')
        self.assertEqual(platform.flavor, 'posix')

    def test_linux(self):
        platform = host.platform_info('linux')
        self.assertEqual(platform.name, 'linux')
        self.assertEqual(platform.flavor, 'posix')

    def test_windows(self):
        platform = host.platform_info('windows')
        self.assertEqual(platform.name, 'windows')
        self.assertEqual(platform.flavor, 'windows')

    def test_unknown(self):
        platform = host.platform_info('unknown')
        self.assertEqual(platform.name, 'unknown')
        self.assertEqual(platform.flavor, 'posix')
