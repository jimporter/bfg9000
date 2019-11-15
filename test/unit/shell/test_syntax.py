from six.moves import cStringIO as StringIO

from .. import *

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.shell.syntax import *


class my_safe_str(safe_str.safe_string):
    pass


class TestWriteString(TestCase):
    def test_variable(self):
        out = Writer(StringIO())
        out.write('foo', Syntax.variable)
        out.write('$bar', Syntax.variable)
        self.assertEqual(out.stream.getvalue(), 'foo$bar')

    def test_shell(self):
        out = Writer(StringIO())
        out.write('foo', Syntax.shell)
        out.write('$bar', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), "foo'$bar'")


class TestWriteLiteral(TestCase):
    def test_variable(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('$foo'), Syntax.variable)
        self.assertEqual(out.stream.getvalue(), '$foo')

    def test_shell(self):
        out = Writer(StringIO())
        out.write(safe_str.literal('$foo'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$foo')


class TestWriteJbos(TestCase):
    def test_variable(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('bar'))
        out.write(s, Syntax.variable)
        self.assertEqual(out.stream.getvalue(), '$foobar')

    def test_shell(self):
        out = Writer(StringIO())
        s = safe_str.jbos('$foo', safe_str.literal('bar'))
        out.write(s, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), "'$foo'bar")


class TestWritePath(PathTestCase):
    def test_variable(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.InstallRoot.bindir), Syntax.variable)
        self.assertEqual(out.stream.getvalue(),
                         self.ospath.join('${bindir}', 'foo'))

    def test_shell(self):
        out = Writer(StringIO())
        out.write(self.Path('foo', path.InstallRoot.bindir), Syntax.shell)
        self.assertEqual(out.stream.getvalue(),
                         "'" + self.ospath.join('${bindir}', 'foo') + "'")


class TestWriteInvalid(TestCase):
    def test_invalid(self):
        out = Writer(StringIO())
        with self.assertRaises(TypeError):
            out.write(my_safe_str(), Syntax.variable)


class TestWriteEach(TestCase):
    def test_basic(self):
        out = Writer(StringIO())
        out.write_each(['foo', 'bar'], Syntax.variable)
        self.assertEqual(out.stream.getvalue(), 'foo bar')

    def test_delims(self):
        out = Writer(StringIO())
        out.write_each(['foo', 'bar'], Syntax.variable, ',', '[', ']')
        self.assertEqual(out.stream.getvalue(), '[foo,bar]')


class TestVariable(TestCase):
    def test_equality(self):
        self.assertTrue(Variable('foo') == Variable('foo'))
        self.assertFalse(Variable('foo') != Variable('foo'))

        self.assertFalse(Variable('foo') == Variable('bar'))
        self.assertTrue(Variable('foo') != Variable('bar'))

    def test_concat_str(self):
        self.assertEqual(Variable('foo') + 'bar', safe_str.jbos(
            safe_str.literal('${foo}'), 'bar'
        ))
        self.assertEqual('foo' + Variable('bar'), safe_str.jbos(
            'foo', safe_str.literal('${bar}')
        ))

    def test_concat_path(self):
        self.assertEqual(Variable('foo') + path.Path('bar'), safe_str.jbos(
            safe_str.literal('${foo}'), path.Path('bar')
        ))
        self.assertEqual(path.Path('foo') + Variable('bar'), safe_str.jbos(
            path.Path('foo'), safe_str.literal('${bar}')
        ))

    def test_concat_var(self):
        self.assertEqual(Variable('foo') + Variable('bar'), safe_str.jbos(
            safe_str.literal('${foo}'), safe_str.literal('${bar}')
        ))

    def test_hash(self):
        self.assertEqual(hash(Variable('foo')), hash(Variable('foo')))
