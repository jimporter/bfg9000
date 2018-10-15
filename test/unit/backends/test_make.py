import ntpath
import os.path
import posixpath
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.make.syntax import *
from bfg9000.platforms import platform_name
from bfg9000.platforms.posix import PosixPath
from bfg9000.platforms.windows import WindowsPath

esc_colon = ':' if platform_name() == 'windows' else '\\:'


def quoted(s):
    return "'" + s + "'"


class TestPattern(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(Pattern('%.c') == Pattern('%.c'))
        self.assertFalse(Pattern('%.c') != Pattern('%.c'))

        self.assertFalse(Pattern('%.c') == Pattern('%.h'))
        self.assertTrue(Pattern('%.c') != Pattern('%.h'))


class TestVariable(unittest.TestCase):
    def test_equality(self):
        self.assertTrue(Variable('foo') == Variable('foo'))
        self.assertFalse(Variable('foo') != Variable('foo'))

        self.assertFalse(Variable('foo') == Variable('bar'))
        self.assertTrue(Variable('foo') != Variable('bar'))


class TestWriteString(unittest.TestCase):
    def test_target(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

    def test_dependency(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

    def test_function(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz$,quux'))

    def test_shell(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz,quux'))

    def test_clean(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')


class TestWriteLiteral(unittest.TestCase):
    def test_target(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.target)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_dependency(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'),
                  Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_function(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.function)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')


class TestWriteShellLiteral(unittest.TestCase):
    def test_target(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

    def test_dependency(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                  Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

    def test_function(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                  Syntax.function)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz$,quux')

    def test_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

    def test_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')


class TestWriteJbos(unittest.TestCase):
    def test_target(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.target)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_dependency(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_function(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_shell(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_clean(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')


class TestWritePath(unittest.TestCase):
    Path = path.Path
    ospath = os.path

    def test_target(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))

    def test_dependency(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))

    def test_function(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.function)
        self.assertEqual(out.stream.getvalue(),
                         quoted(self.ospath.join('$(srcdir)', 'foo')))

    def test_shell(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.shell)
        self.assertEqual(out.stream.getvalue(),
                         quoted(self.ospath.join('$(srcdir)', 'foo')))

    def test_clean(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.Root.srcdir), Syntax.clean)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))


class TestWritePosixPath(TestWritePath):
    Path = PosixPath
    ospath = posixpath


class TestWriteWindowsPath(TestWritePath):
    Path = WindowsPath
    ospath = ntpath


class TestMakefile(unittest.TestCase):
    def setUp(self):
        self.makefile = Makefile('build.bfg')

    def test_variable(self):
        var = self.makefile.variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.makefile._write_variable(out, var, 'value')
        self.assertEqual(out.stream.getvalue(), 'name := value\n')

        var = self.makefile.variable('name', 'value2', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        self.assertRaises(ValueError, self.makefile.variable, 'name', 'value')

    def test_target_variable(self):
        var = self.makefile.target_variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.makefile._write_variable(out, var, 'value', target=Pattern('%'))
        self.assertEqual(out.stream.getvalue(), '%: name := value\n')

        var = self.makefile.target_variable('name', 'value2', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        self.assertRaises(ValueError, self.makefile.target_variable, 'name',
                          'value')

    def test_define(self):
        var = self.makefile.define('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.makefile._write_define(out, *self.makefile._defines[0])
        self.assertEqual(out.stream.getvalue(),
                         'define name\nvalue\nendef\n\n')

        var = self.makefile.define('name', 'value', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        var = self.makefile.define('multi', ['value1', 'value2'])
        self.assertEqual(var, Variable('multi'))
        out = Writer(StringIO())
        self.makefile._write_define(out, *self.makefile._defines[1])
        self.assertEqual(out.stream.getvalue(),
                         'define multi\nvalue1\nvalue2\nendef\n\n')

        self.assertRaises(ValueError, self.makefile.define, 'name', 'value')

    def test_rule(self):
        self.makefile.rule('target', variables={'name': 'value'},
                           recipe=['cmd'])
        out = Writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[0])
        self.assertEqual(out.stream.getvalue(),
                         'target: name := value\n'
                         'target:\n'
                         '\tcmd\n\n')
