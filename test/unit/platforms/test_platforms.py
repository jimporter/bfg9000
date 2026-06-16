from unittest import mock

from . import mock_uname
from .. import *

from bfg9000 import platforms


class TestPlatformName(TestCase):
    def setUp(self):
        platforms.platform_name._reset()

    def tearDown(self):
        platforms.platform_name._reset()

    def test_linux(self):
        with mock_uname(os='GNU/Linux', lsb='Ubuntu'):
            self.assertEqual(platforms.platform_name(), 'linux')

    def test_linux_no_lsb(self):
        with mock_uname(os='GNU/Linux', lsb=OSError()):
            self.assertEqual(platforms.platform_name(), 'linux')

    def test_android(self):
        with mock_uname(os='GNU/Linux', lsb='Android'):
            self.assertEqual(platforms.platform_name(), 'android')

    def test_macos(self):
        with mock_uname(os='Darwin', machine='ARM64'):
            self.assertEqual(platforms.platform_name(), 'macos')

    def test_ios(self):
        with mock_uname(os='Darwin', machine='iPhone'):
            self.assertEqual(platforms.platform_name(), 'ios')

    def test_windows_nt(self):
        with mock_uname(os=OSError()), \
             mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='3.10.528'):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_windows_10(self):
        with mock_uname(os=OSError()), \
             mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='10'):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_windows_9x(self):
        with mock_uname(os=OSError()), \
             mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='4.10.1998'):
            self.assertEqual(platforms.platform_name(), 'win9x')

    def test_windows_3x(self):
        with mock_uname(os=OSError()), \
             mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='3.11'):
            self.assertEqual(platforms.platform_name(), 'msdos')

    def test_windows_with_msys_uname(self):
        with mock_uname(os='Msys'), \
             mock.patch('platform.system', return_value='Windows'), \
             mock.patch('platform.version', return_value='10'):
            self.assertEqual(platforms.platform_name(), 'winnt')

    def test_cygwin(self):
        with mock_uname(os='Cygwin'):
            self.assertEqual(platforms.platform_name(), 'cygwin')

    def test_unknown(self):
        with mock_uname(os='Goofy'):
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
