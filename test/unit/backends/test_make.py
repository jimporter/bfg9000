import os
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.make.syntax import *
from bfg9000.platforms import platform_name

esc_colon = ':' if platform_name() == 'windows' else '\\:'


def quoted(s):
    return "'" + s + "'"


class TestMakeWriter(unittest.TestCase):
    # strings
    def test_write_string_target(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

    def test_write_string_dependency(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

    def test_write_string_function(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz$,quux'))

    def test_write_string_shell(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz,quux'))

    def test_write_string_clean(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

    # literals
    def test_write_literal_target(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.target)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_write_literal_dependency(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'),
                  Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_write_literal_function(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.function)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_write_literal_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_write_literal_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar|baz,quux')

    # shell literals
    def test_write_shell_literal_target(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

    def test_write_shell_literal_dependency(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                  Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

    def test_write_shell_literal_function(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                  Syntax.function)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz$,quux')

    def test_write_shell_literal_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

    def test_write_shell_literal_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.shell_literal('foo: $bar|baz,quux'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

    # jbos
    def test_write_jbos_target(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.target)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_write_jbos_dependency(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_write_jbos_function(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_write_jbos_shell(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_write_jbos_clean(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        out.write(s, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    # paths
    def test_write_path_target(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         os.path.join('$(srcdir)', 'foo'))

    def test_write_path_dependency(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         os.path.join('$(srcdir)', 'foo'))

    def test_write_path_function(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.function)
        self.assertEqual(out.stream.getvalue(),
                         quoted(os.path.join('$(srcdir)', 'foo')))

    def test_write_path_shell(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.shell)
        self.assertEqual(out.stream.getvalue(),
                         quoted(os.path.join('$(srcdir)', 'foo')))

    def test_write_path_clean(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.clean)
        self.assertEqual(out.stream.getvalue(),
                         os.path.join('$(srcdir)', 'foo'))
