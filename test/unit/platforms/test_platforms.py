import mock
import unittest

from bfg9000 import platforms


class TestPlatformName(unittest.TestCase):
    def setUp(self):
        platforms.platform_name._reset()

    def tearDown(self):
        platforms.platform_name._reset()

    def test_linux(self):
        with mock.patch('platform.system', lambda: 'Linux'):
            self.assertEqual(platforms.platform_name(), 'linux')

    def test_macos(self):
        with mock.patch('platform.system', lambda: 'Darwin'):
            self.assertEqual(platforms.platform_name(), 'darwin')

    def test_windows(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('platform.system', lambda: 'Windows'), \
             mock.patch('subprocess.check_output', mock_execute):  # noqa:
            self.assertEqual(platforms.platform_name(), 'windows')

    def test_windows_with_uname(self):
        def mock_execute(*args, **kwargs):
            return 'foobar'

        with mock.patch('platform.system', lambda: 'Windows'), \
             mock.patch('subprocess.check_output', mock_execute):  # noqa:
            self.assertEqual(platforms.platform_name(), 'windows')

    def test_cygwin(self):
        with mock.patch('platform.system', lambda: 'CYGWIN_NT-6.1-WOW64'):
            self.assertEqual(platforms.platform_name(), 'cygwin')

    def test_cygwin_native_python(self):
        def mock_execute(*args, **kwargs):
            return 'CYGWIN_NT-6.1-WOW64'

        with mock.patch('platform.system', lambda: 'Windows'), \
             mock.patch('subprocess.check_output', mock_execute):  # noqa
            self.assertEqual(platforms.platform_name(), 'cygwin')
