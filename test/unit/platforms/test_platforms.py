from unittest import mock

from .. import *

from bfg9000 import platforms


class TestPlatformName(TestCase):
    def setUp(self):
        platforms.platform_name._reset()

    def tearDown(self):
        platforms.platform_name._reset()

    def test_linux(self):
        with mock.patch('platform.system', return_value='Linux'):
            self.assertEqual(platforms.platform_name(), 'linux')

    def test_linux_no_lsb(self):
        with mock.patch('platform.system', return_value='Linux'), \
             mock.patch('subprocess.check_output', side_effect=OSError()):
            self.assertEqual(platforms.platform_name(), 'linux')

    def test_android(self):
        with mock.patch('platform.system', return_value='Linux'), \
             mock.patch('subprocess.check_output', return_value='Android'):
            self.assertEqual(platforms.platform_name(), 'android')

    def test_macos(self):
        with mock.patch('platform.system', return_value='Darwin'):
            self.assertEqual(platforms.platform_name(), 'macos')

    def test_ios(self):
        with mock.patch('platform.system', return_value='Darwin'), \
             mock.patch('platform.machine', return_value='iPhone'):
            self.assertEqual(platforms.platform_name(), 'ios')

    def test_windows_nt(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='3.10.528'), \
             mock.patch('subprocess.check_output', side_effect=OSError()):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_windows_10(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='10'), \
             mock.patch('subprocess.check_output', side_effect=OSError()):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_windows_9x(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='4.10.1998'), \
             mock.patch('subprocess.check_output', side_effect=OSError()):
            self.assertEqual(platforms.platform_name(), 'win9x')

    def test_windows_3x(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='3.11'), \
             mock.patch('subprocess.check_output', side_effect=OSError()):
            self.assertEqual(platforms.platform_name(), 'msdos')

    def test_windows_with_uname(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='10'), \
             mock.patch('subprocess.check_output', return_value='foobar'):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_cygwin(self):
        with mock.patch('platform.system', return_value='CYGWIN_NT-6.1-WOW64'):
            self.assertEqual(platforms.platform_name(), 'cygwin')

    def test_cygwin_native_python(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('subprocess.check_output',
                        return_value='CYGWIN_NT-6.1-WOW64'):
            self.assertEqual(platforms.platform_name(), 'cygwin')

    def test_unknown(self):
        with mock.patch('platform.system', return_value='Goofy'):
            self.assertEqual(platforms.platform_name(), 'goofy')


class TestPlatformTuple(TestCase):
    def setUp(self):
        platforms.platform_name._reset()

    def tearDown(self):
        platforms.platform_name._reset()

    def test_info(self):
        self.assertEqual(platforms.platform_tuple()[1],
                         platforms.platform_name())


class TestParseTriplet(TestCase):
    def test_with_vendor(self):
        Triplet = platforms.PlatformTriplet
        self.assertEqual(platforms.parse_triplet('i686-pc-linux-gnu'),
                         Triplet('i686', 'pc', 'linux', 'gnu'))
        self.assertEqual(platforms.parse_triplet('i686-pc-win32'),
                         Triplet('i686', 'pc', 'win32', None))

    def test_without_vendor(self):
        Triplet = platforms.PlatformTriplet
        self.assertEqual(platforms.parse_triplet('x86_64-linux-gnu'),
                         Triplet('x86_64', 'unknown', 'linux', 'gnu'))
        self.assertEqual(platforms.parse_triplet('x86_64-win32'),
                         Triplet('x86_64', 'unknown', 'win32', None))

    def test_invalid(self):
        parse_triplet = platforms.parse_triplet
        self.assertRaises(ValueError, parse_triplet, 'x86_64')
        self.assertRaises(ValueError, parse_triplet, 'x86_64-gnu')
        self.assertRaises(ValueError, parse_triplet, 'x86_64-linux-gnu-extra')
        self.assertRaises(ValueError, parse_triplet, 'i686-pc-linux-gnu-extra')
