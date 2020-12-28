import sys
from unittest import mock

from .. import *

from bfg9000.path import Root
from bfg9000.safe_str import jbos
from bfg9000.shell import (CalledProcessError, convert_args, execute, Mode,
                           split_paths, which)

base_dirs = {
    Root.srcdir: '$(srcdir)',
    Root.builddir: None,
}


class TestSplitPaths(TestCase):
    def test_empty(self):
        self.assertEqual(split_paths(''), [])

    def test_single(self):
        self.assertEqual(split_paths('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(split_paths('foo:bar', ':'), ['foo', 'bar'])


class TestWhich(TestCase):
    def setUp(self):
        self.env = {'PATH': '/usr/bin{}/usr/local/bin'.format(os.pathsep)}

    def test_simple(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('python', env=self.env), ['python'])

    def test_multiword(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('python --foo', env=self.env),
                             ['python', '--foo'])

    def test_abs(self):
        with mock.patch('os.path.exists', return_value=True):
            self.assertEqual(which('/path/to/python', env=self.env),
                             ['/path/to/python'])

    def test_multiple(self):
        with mock.patch('os.path.exists', side_effect=[False, False, True]):
            self.assertEqual(which(['python', 'python3'], env=self.env),
                             ['python3'])

    def test_multiple_args(self):
        with mock.patch('os.path.exists', side_effect=[False, False, True]):
            self.assertEqual(which(['python', ['python3', '--foo']],
                                   env=self.env), ['python3', '--foo'])

    def test_resolve(self):
        with mock.patch('os.path.exists', side_effect=[False, True]):
            self.assertEqual(which('python', env=self.env, resolve=True),
                             [os.path.normpath('/usr/local/bin/python')])

    def test_path_ext(self):
        class MockInfo:
            has_path_ext = True

        env = {'PATH': '/usr/bin', 'PATHEXT': '.exe'}
        with mock.patch('bfg9000.shell.platform_info', MockInfo), \
             mock.patch('os.path.exists', side_effect=[False, True]):  # noqa
            self.assertEqual(which('python', env=env), ['python'])

        with mock.patch('bfg9000.shell.platform_info', MockInfo), \
             mock.patch('os.path.exists', side_effect=[False, True]):  # noqa
            self.assertEqual(which('python', env=env, resolve=True),
                             [os.path.normpath('/usr/bin/python.exe')])

        with mock.patch('bfg9000.shell.platform_info', MockInfo), \
             mock.patch('os.path.exists', side_effect=[False, True]):  # noqa
            self.assertEqual(
                which([['python', '--foo']], env=env, resolve=True),
                [os.path.normpath('/usr/bin/python.exe'), '--foo']
            )

    def test_not_found(self):
        with mock.patch('os.path.exists', return_value=False):
            self.assertRaises(IOError, which, 'python')

    def test_empty(self):
        self.assertRaises(TypeError, which, [])


class TestConvertArgs(PathTestCase):
    def test_string(self):
        self.assertEqual(convert_args(['foo', 'bar']), ['foo', 'bar'])

    def test_path(self):
        self.assertEqual(convert_args([self.Path('/foo')]),
                         [self.ospath.sep + 'foo'])
        self.assertEqual(convert_args([self.Path('foo')], base_dirs), ['foo'])
        self.assertEqual(convert_args([self.Path('foo', Root.srcdir)],
                                      base_dirs),
                         [self.ospath.join('$(srcdir)', 'foo')])

        self.assertRaises(TypeError, convert_args, [self.Path('foo')])

    def test_jbos(self):
        self.assertEqual(convert_args([jbos('foo', 'bar')]), ['foobar'])
        self.assertEqual(convert_args([jbos('foo', self.Path('/bar'))]),
                         ['foo' + self.ospath.sep + 'bar'])


class TestExecute(TestCase):
    def test_no_output(self):
        self.assertEqual(execute([sys.executable, '-c', 'exit()']), None)

    def test_stdout(self):
        self.assertEqual(execute([sys.executable, '-c', 'print("hello")'],
                                 stdout=Mode.pipe), 'hello\n')

    def test_stderr(self):
        self.assertEqual(execute(
            [sys.executable, '-c', 'import sys; sys.stderr.write("hello\\n")'],
            stderr=Mode.pipe
        ), 'hello\n')

    def test_stdout_stderr(self):
        self.assertEqual(execute(
            [sys.executable, '-c',
             'import sys; sys.stdout.write("stdout\\n"); ' +
             'sys.stderr.write("stderr\\n");'],
            stdout=Mode.pipe, stderr=Mode.pipe
        ), ('stdout\n', 'stderr\n'))

    def test_returncode(self):
        self.assertEqual(execute([sys.executable, '-c', 'exit(1)'],
                                 returncode=1), None)
        self.assertEqual(execute([sys.executable, '-c', 'exit(1)'],
                                 returncode=[1, 2]), None)
        self.assertEqual(execute([sys.executable, '-c', 'exit(1)'],
                                 returncode='any'), None)
        self.assertEqual(execute([sys.executable, '-c', 'exit(1)'],
                                 returncode='fail'), None)

        with self.assertRaises(CalledProcessError):
            self.assertEqual(execute([sys.executable, '-c', 'exit(1)']), None)
        with self.assertRaises(CalledProcessError):
            self.assertEqual(execute([sys.executable, '-c', 'exit(0)'],
                                     returncode='fail'), None)

    def test_shell(self):
        self.assertEqual(execute('echo hello', shell=True, stdout=Mode.pipe),
                         'hello\n')
