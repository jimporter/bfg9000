import ntpath
import os.path
import posixpath
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.ninja.syntax import *
from bfg9000.file_types import File
from bfg9000.platforms.host import platform_info
from bfg9000.platforms.posix import PosixPath
from bfg9000.platforms.windows import WindowsPath

quote_char = '"' if platform_info().family == 'windows' else "'"


def quoted(s):
    return quote_char + s + quote_char


class TestVariable(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(Variable('foo') == Variable('foo'))
        self.assertFalse(Variable('foo') != Variable('foo'))

        self.assertFalse(Variable('foo') == Variable('bar'))
        self.assertTrue(Variable('foo') != Variable('bar'))


class TestWriteString(unittest.TestCase):
    def test_output(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.output)
        self.assertEqual(out.stream.getvalue(), 'foo$:$ $$bar')

    def test_input(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.input)
        self.assertEqual(out.stream.getvalue(), 'foo:$ $$bar')

    def test_shell(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar'))

    def test_clean(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar')


class TestWriteLiteral(unittest.TestCase):
    def test_output(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar'), Syntax.output)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_input(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar'), Syntax.input)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')


class TestWriteShellLiteral(unittest.TestCase):
    def test_output(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar'), Syntax.output)
        self.assertEqual(out.stream.getvalue(), 'foo$:$ $$bar')

    def test_input(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar'), Syntax.input)
        self.assertEqual(out.stream.getvalue(), 'foo:$ $$bar')

    def test_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar')

    def test_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar')


class TestWriteJbos(unittest.TestCase):
    def test_output(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.output)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_input(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.input)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_shell(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.shell)
        if platform_info().family == 'windows':
            expected = '$$foo$bar'
        else:
            expected = quoted('$$foo') + '$bar'
        self.assertEqual(out.stream.getvalue(), expected)

    def test_clean(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')


class TestWritePath(unittest.TestCase):
    Path = path.Path
    ospath = os.path

    def test_output(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.output)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('${srcdir}', 'foo'))

    def test_input(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.input)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('${srcdir}', 'foo'))

    def test_shell(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.shell)
        self.assertEqual(out.stream.getvalue(),
                         quoted(self.ospath.join('${srcdir}', 'foo')))

    def test_clean(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.clean)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('${srcdir}', 'foo'))


class TestWritePosixPath(TestWritePath):
    Path = PosixPath
    ospath = posixpath


class TestWriteWindowsPath(TestWritePath):
    Path = WindowsPath
    ospath = ntpath


class TestNinjaFile(unittest.TestCase):
    def setUp(self):
        self.ninjafile = NinjaFile('build.bfg')

    def test_variable(self):
        var = self.ninjafile.variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.ninjafile._write_variable(out, var, 'value')
        self.assertEqual(out.stream.getvalue(), 'name = value\n')

        # Test duplicate variables.
        var = self.ninjafile.variable('name', 'value2', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        self.assertRaises(ValueError, self.ninjafile.variable, 'name', 'value')

    def test_rule(self):
        self.ninjafile.rule('my_rule', ['cmd'])
        out = Writer(StringIO())
        self.ninjafile._write_rule(out, 'my_rule',
                                   self.ninjafile._rules['my_rule'])
        self.assertEqual(out.stream.getvalue(),
                         'rule my_rule\n'
                         '  command = cmd\n')

        # Test duplicate rules.
        self.assertRaises(ValueError, self.ninjafile.rule, 'my_rule', ['cmd'])

    def test_build(self):
        self.ninjafile.rule('my_rule', ['cmd'])
        self.ninjafile.build('output', 'my_rule')

        out = Writer(StringIO())
        self.ninjafile._write_build(out, self.ninjafile._builds[0])
        self.assertEqual(out.stream.getvalue(), 'build output: my_rule\n')

        # Test duplicate targets.
        self.assertRaises(ValueError, self.ninjafile.build, 'output',
                          'my_rule')
        self.assertRaises(ValueError, self.ninjafile.build,
                          ['output', 'output2'], 'my_rule')
        self.assertRaises(ValueError, self.ninjafile.build,
                          File(path.Path('output', path.Root.builddir)),
                          'my_rule')
