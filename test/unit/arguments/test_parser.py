from unittest import mock

from .. import *

from bfg9000 import path
from bfg9000.arguments import parser


class TestEnableAction(TestCase):
    action = 'enable'
    not_action = 'disable'

    def test_basic(self):
        p = parser.ArgumentParser()
        p.add_argument('--feature', action=self.action)

        self.assertEqual(p.parse_args([]), parser.Namespace(feature=False))
        self.assertEqual(p.parse_args(['--{}-feature'.format(self.action)]),
                         parser.Namespace(feature=True))
        self.assertEqual(p.parse_args(
            ['--{}-feature'.format(self.not_action)]
        ), parser.Namespace(feature=False))

    def test_default(self):
        p = parser.ArgumentParser()
        p.add_argument('--feature', action=self.action, default=True)

        self.assertEqual(p.parse_args([]), parser.Namespace(feature=True))
        self.assertEqual(p.parse_args(['--{}-feature'.format(self.action)]),
                         parser.Namespace(feature=True))
        self.assertEqual(p.parse_args(
            ['--{}-feature'.format(self.not_action)]
        ), parser.Namespace(feature=False))

    def test_invalid(self):
        p = parser.ArgumentParser()
        with self.assertRaises(ValueError):
            p.add_argument('feature', action=self.action)
        with self.assertRaises(ValueError):
            p.add_argument('-f', action=self.action)


class TestWithAction(TestEnableAction):
    action = 'with'
    not_action = 'without'


class TestDirectory(TestCase):
    def test_existent(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isdir', return_value=True):
            self.assertPathEqual(parser.Directory()('foo'),
                                 path.abspath('foo/', absdrive=False))
            self.assertPathEqual(parser.Directory(True)('foo'),
                                 path.abspath('foo/', absdrive=False))

    def test_not_dir(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isdir', return_value=False):
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory()('foo')
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory(True)('foo')

    def test_nonexistent(self):
        with mock.patch('bfg9000.path.exists', return_value=False):
            self.assertPathEqual(parser.Directory()('foo'),
                                 path.abspath('foo/', absdrive=False))
            with self.assertRaises(parser.ArgumentTypeError):
                parser.Directory(True)('foo')


class TestFile(TestCase):
    def test_existent(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isfile', return_value=True):
            self.assertPathEqual(parser.File()('foo'),
                                 path.abspath('foo', absdrive=False))
            self.assertPathEqual(parser.File(True)('foo'),
                                 path.abspath('foo', absdrive=False))

    def test_not_file(self):
        with mock.patch('bfg9000.path.exists', return_value=True), \
             mock.patch('bfg9000.path.isfile', return_value=False):
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File()('foo')
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File(True)('foo')

    def test_nonexistent(self):
        with mock.patch('bfg9000.path.exists', return_value=False):
            self.assertPathEqual(parser.File()('foo'),
                                 path.abspath('foo', absdrive=False))
            with self.assertRaises(parser.ArgumentTypeError):
                parser.File(True)('foo')


class TestParser(TestCase):
    def test_short_value(self):
        p = parser.ArgumentParser()
        p.add_argument('-f')

        self.assertEqual(p.parse_args([]), parser.Namespace(f=None))
        self.assertEqual(p.parse_args(['-fbar']), parser.Namespace(f='bar'))

    def test_short_flag(self):
        p = parser.ArgumentParser()
        p.add_argument('-f', action='store_true')

        self.assertEqual(p.parse_args([]), parser.Namespace(f=False))
        self.assertEqual(p.parse_args(['-f']), parser.Namespace(f=True))

    def test_long_value(self):
        p = parser.ArgumentParser()
        p.add_argument('--foo')

        self.assertEqual(p.parse_args([]), parser.Namespace(foo=None))
        self.assertEqual(p.parse_args(['--foo', 'bar']),
                         parser.Namespace(foo='bar'))
        self.assertEqual(p.parse_args(['--foo=bar']),
                         parser.Namespace(foo='bar'))
        self.assertEqual(p.parse_known_args(['--fo=bar']),
                         (parser.Namespace(foo=None), ['--fo=bar']))

    def test_long_flag(self):
        p = parser.ArgumentParser()
        p.add_argument('--foo', action='store_true')

        self.assertEqual(p.parse_args([]), parser.Namespace(foo=False))
        self.assertEqual(p.parse_args(['--foo']), parser.Namespace(foo=True))
        self.assertEqual(p.parse_known_args(['--fo']),
                         (parser.Namespace(foo=False), ['--fo']))

    def test_positional(self):
        p = parser.ArgumentParser()
        p.add_argument('foo')

        self.assertEqual(p.parse_args(['bar']), parser.Namespace(foo='bar'))

    def test_group(self):
        p = parser.ArgumentParser()
        g = p.add_argument_group()

        g.add_argument('--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), parser.Namespace(foo=True))

        g.value = True
        self.assertTrue(g.value)
        del g.value
        self.assertFalse(hasattr(g, 'value'))

    def test_complete(self):
        p = parser.ArgumentParser()
        arg = p.add_argument('--arg', complete='file')
        self.assertEqual(arg.complete, 'file')

        file_arg = p.add_argument('--file', type=parser.File())
        self.assertEqual(file_arg.complete, 'file')

        dir_arg = p.add_argument('--dir', type=parser.Directory())
        self.assertEqual(dir_arg.complete, 'directory')


class TestUserArgument(TestCase):
    def test_parse(self):
        p = parser.ArgumentParser()
        p.usage = 'parse'

        parser.add_user_argument(p, '--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), parser.Namespace(foo=True))
        self.assertEqual(p.parse_args(['--x-foo']),
                         parser.Namespace(foo=True))

    def test_group(self):
        p = parser.ArgumentParser()
        g = p.add_argument_group()
        g.usage = 'parse'

        parser.add_user_argument(g, '--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), parser.Namespace(foo=True))
        self.assertEqual(p.parse_args(['--x-foo']),
                         parser.Namespace(foo=True))

    def test_help(self):
        p = parser.ArgumentParser()
        p.usage = 'help'

        parser.add_user_argument(p, '--foo', action='store_true')
        self.assertEqual(p.parse_args(['--foo']), parser.Namespace(foo=True))
        self.assertEqual(p.parse_known_args(['--x-foo']),
                         (parser.Namespace(foo=False), ['--x-foo']))

    def test_invalid(self):
        add_user_argument = parser.add_user_argument
        p = parser.ArgumentParser()
        p.usage = 'parse'

        self.assertRaises(ValueError, add_user_argument, p, '-f')
        self.assertRaises(ValueError, add_user_argument, p, 'foo')
        self.assertRaises(ValueError, add_user_argument, p, '--foo', '-f')
        self.assertRaises(ValueError, add_user_argument, p, '--x-foo')
