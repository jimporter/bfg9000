import ntpath
import os.path
import posixpath
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.ninja.syntax import *
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
