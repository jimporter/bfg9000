import os
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.ninja.syntax import *
from bfg9000.platforms import platform_name

quote_char = '"' if platform_name() == 'windows' else "'"


def quoted(s):
    return quote_char + s + quote_char


class TestNinjaWriter(unittest.TestCase):
    # strings
    def test_write_string_output(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.output)
        self.assertEqual(out.stream.getvalue(), 'foo$:$ $$bar')

    def test_write_string_input(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.input)
        self.assertEqual(out.stream.getvalue(), 'foo:$ $$bar')

    def test_write_string_shell(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar'))

    def test_write_string_clean(self):
        out = Writer(StringIO())
        out.write('foo: $bar', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar')

    # escaped strings
    def test_write_escaped_string_output(self):
        out = Writer(StringIO())
        out.write(safe_str.escaped_str('foo: $bar'), Syntax.output)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_write_escaped_string_input(self):
        out = Writer(StringIO())
        out.write(safe_str.escaped_str('foo: $bar'), Syntax.input)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_write_escaped_string_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.escaped_str('foo: $bar'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    def test_write_escaped_string_clean(self):
        out = Writer(StringIO())
        out.write(safe_str.escaped_str('foo: $bar'), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $bar')

    # jbos
    def test_write_jbos_output(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.escaped_str('$bar'))
        out.write(s, Syntax.output)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_write_jbos_input(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.escaped_str('$bar'))
        out.write(s, Syntax.input)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    def test_write_jbos_shell(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.escaped_str('$bar'))
        out.write(s, Syntax.shell)
        if platform_name() == 'windows':
            expected = '$$foo$bar'
        else:
            expected = quoted('$$foo') + '$bar'
        self.assertEqual(out.stream.getvalue(), expected)

    def test_write_jbos_clean(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.escaped_str('$bar'))
        out.write(s, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$$foo$bar')

    # paths
    def test_write_path_output(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.output)
        self.assertEqual(out.stream.getvalue(), os.path.join('$srcdir', 'foo'))

    def test_write_path_input(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.input)
        self.assertEqual(out.stream.getvalue(), os.path.join('$srcdir', 'foo'))

    def test_write_path_shell(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.shell)
        self.assertEqual(out.stream.getvalue(),
                         quoted(os.path.join('$srcdir', 'foo')))

    def test_write_path_clean(self):
        out = Writer(StringIO())
        out.write(path.Path('foo', path.Root.srcdir), Syntax.clean)
        self.assertEqual(out.stream.getvalue(), os.path.join('$srcdir', 'foo'))
