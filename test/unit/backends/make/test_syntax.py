from io import StringIO

from ... import *

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.make.syntax import *
from bfg9000.file_types import File
from bfg9000.platforms.host import platform_info

esc_colon = ':' if platform_info().family == 'windows' else '\\:'


def quoted(s):
    return "'" + s + "'"


class my_safe_str(safe_str.safe_string):
    pass


class TestPattern(TestCase):
    def test_equality(self):
        self.assertTrue(Pattern('%.c') == Pattern('%.c'))
        self.assertFalse(Pattern('%.c') != Pattern('%.c'))

        self.assertFalse(Pattern('%.c') == Pattern('%.h'))
        self.assertTrue(Pattern('%.c') != Pattern('%.h'))

        self.assertTrue(Pattern('%\\%.c') == Pattern('%\\%.c'))
        self.assertFalse(Pattern('%\\%.c') != Pattern('%\\%.c'))

    def test_concat_str(self):
        self.assertEqual(Pattern('%.c') + 'bar', safe_str.jbos(
            safe_str.literal('%'), '.cbar'
        ))
        self.assertEqual('foo' + Pattern('%.h'), safe_str.jbos(
            'foo', safe_str.literal('%'), '.h'
        ))

    def test_concat_path(self):
        self.assertEqual(Pattern('%.c') + path.Path('bar'), safe_str.jbos(
            safe_str.literal('%'), '.c', path.Path('bar')
        ))
        self.assertEqual(path.Path('foo') + Pattern('%.h'), safe_str.jbos(
            path.Path('foo'), safe_str.literal('%'), '.h'
        ))

    def test_concat_pattern(self):
        self.assertEqual(Pattern('%.c') + Pattern('%.h'), safe_str.jbos(
            safe_str.literal('%'), '.c', safe_str.literal('%'), '.h'
        ))

    def test_hash(self):
        self.assertEqual(hash(Pattern('%.c')), hash(Pattern('%.c')))

    def test_invalid(self):
        self.assertRaises(ValueError, Pattern, '.c')
        self.assertRaises(ValueError, Pattern, '%%.c')
        self.assertRaises(ValueError, Pattern, '%\\\\%.c')


class TestVariable(TestCase):
    def test_equality(self):
        self.assertTrue(Variable('foo') == Variable('foo'))
        self.assertFalse(Variable('foo') != Variable('foo'))

        self.assertFalse(Variable('foo') == Variable('bar'))
        self.assertTrue(Variable('foo') != Variable('bar'))

    def test_concat_str(self):
        self.assertEqual(Variable('foo') + 'bar', safe_str.jbos(
            safe_str.literal('$(foo)'), 'bar'
        ))
        self.assertEqual('foo' + Variable('bar'), safe_str.jbos(
            'foo', safe_str.literal('$(bar)')
        ))

        self.assertEqual(Variable('foo', True) + 'bar', safe_str.jbos(
            safe_str.literal("'$(foo)'"), 'bar'
        ))
        self.assertEqual('foo' + Variable('bar', True), safe_str.jbos(
            'foo', safe_str.literal("'$(bar)'")
        ))

    def test_concat_path(self):
        self.assertEqual(Variable('foo') + path.Path('bar'), safe_str.jbos(
            safe_str.literal('$(foo)'), path.Path('bar')
        ))
        self.assertEqual(path.Path('foo') + Variable('bar'), safe_str.jbos(
            path.Path('foo'), safe_str.literal('$(bar)')
        ))

        self.assertEqual(
            Variable('foo', True) + path.Path('bar'),
            safe_str.jbos(safe_str.literal("'$(foo)'"), path.Path('bar'))
        )
        self.assertEqual(
            path.Path('foo') + Variable('bar', True),
            safe_str.jbos(path.Path('foo'), safe_str.literal("'$(bar)'"))
        )

    def test_concat_var(self):
        self.assertEqual(Variable('foo') + Variable('bar'), safe_str.jbos(
            safe_str.literal('$(foo)'), safe_str.literal('$(bar)')
        ))
        self.assertEqual(
            Variable('foo', True) + Variable('bar'),
            safe_str.jbos(safe_str.literal("'$(foo)'"),
                          safe_str.literal('$(bar)'))
        )

    def test_hash(self):
        self.assertEqual(hash(Variable('foo')), hash(Variable('foo')))

    def test_var(self):
        self.assertFalse(var('foo').quoted)
        self.assertEqual(Variable('foo'), var('foo'))
        self.assertEqual(Variable('foo'), var(Variable('foo')))

    def test_qvar(self):
        self.assertTrue(qvar('foo').quoted)
        self.assertEqual(Variable('foo'), qvar('foo'))
        self.assertEqual(Variable('foo'), qvar(Variable('foo')))


class TestFunction(TestCase):
    def test_equality(self):
        self.assertTrue(Function('fn') == Function('fn'))
        self.assertFalse(Function('fn') != Function('fn'))
        self.assertTrue(Function('fn', '1', '2') == Function('fn', '1', '2'))
        self.assertFalse(Function('fn', '1', '2') != Function('fn', '1', '2'))

        self.assertFalse(Function('fn') == Function('fn2'))
        self.assertTrue(Function('fn') != Function('fn2'))
        self.assertFalse(Function('fn', '1', '2') == Function('fn2', '1', '2'))
        self.assertTrue(Function('fn', '1', '2') != Function('fn2', '1', '2'))
        self.assertFalse(Function('fn', '1', '2') == Function('fn', '1', '3'))
        self.assertTrue(Function('fn', '1', '2') != Function('fn', '1', '3'))
        self.assertFalse(Function('fn', '1', '2') == Function('fn', '1'))
        self.assertTrue(Function('fn', '1', '2') != Function('fn', '1'))

    def test_call(self):
        self.assertEqual(Call('fn', '1', '2'),
                         Function('call', 'fn', '1', '2'))

    def test_concat_str(self):
        self.assertEqual(Function('fn', '1', '2') + 'foo', safe_str.jbos(
            safe_str.literal('$(fn 1,2)'), 'foo'
        ))
        self.assertEqual('foo' + Function('fn', '1', '2'), safe_str.jbos(
            'foo', safe_str.literal('$(fn 1,2)')
        ))

        self.assertEqual(
            Function('fn', '1', '2', quoted=True) + 'foo',
            safe_str.jbos(safe_str.literal("'$(fn 1,2)'"), 'foo')
        )
        self.assertEqual(
            'foo' + Function('fn', '1', '2', quoted=True),
            safe_str.jbos('foo', safe_str.literal("'$(fn 1,2)'")
        ))

    def test_concat_path(self):
        self.assertEqual(
            Function('fn', '1', '2') + path.Path('foo'),
            safe_str.jbos(safe_str.literal('$(fn 1,2)'), path.Path('foo'))
        )
        self.assertEqual(
            path.Path('foo') + Function('fn', '1', '2'),
            safe_str.jbos(path.Path('foo'), safe_str.literal('$(fn 1,2)'))
        )

        self.assertEqual(
            Function('fn', '1', '2', quoted=True) + path.Path('foo'),
            safe_str.jbos(safe_str.literal("'$(fn 1,2)'"), path.Path('foo'))
        )
        self.assertEqual(
            path.Path('foo') + Function('fn', '1', '2', quoted=True),
            safe_str.jbos(path.Path('foo'), safe_str.literal("'$(fn 1,2)'"))
        )

    def test_concat_var(self):
        self.assertEqual(
            Function('foo', '1', '2') + Function('bar', '3', '4'),
            safe_str.jbos(safe_str.literal('$(foo 1,2)'),
                          safe_str.literal('$(bar 3,4)')
        ))
        self.assertEqual(
            Function('foo', '1', '2', quoted=True) + Function('bar', '3', '4'),
            safe_str.jbos(safe_str.literal("'$(foo 1,2)'"),
                          safe_str.literal('$(bar 3,4)')
        ))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            Function('fn', kwarg=True)


class TestSilent(TestCase):
    def test_silent(self):
        v = Variable('foo')
        self.assertIs(Silent(v).data, v)


class TestWriteString(TestCase):
    def test_target(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

        out = Writer(StringIO())
        out.write('~foo', Syntax.target)
        self.assertEqual(out.stream.getvalue(), '\\~foo')

        out = Writer(StringIO())
        out.write('foo~bar ~ baz', Syntax.target)
        self.assertEqual(out.stream.getvalue(), 'foo~bar\\ ~\\ baz')

    def test_dependency(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

        out = Writer(StringIO())
        out.write('~foo', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '\\~foo')

        out = Writer(StringIO())
        out.write('foo~bar ~ baz', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), 'foo~bar\\ ~\\ baz')

    def test_function(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz$,quux'))

        out = Writer(StringIO())
        out.write('~foo', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('~foo'))

        out = Writer(StringIO())
        out.write('foo~bar ~ baz', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo~bar ~ baz'))

    def test_shell(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz,quux'))

        out = Writer(StringIO())
        out.write('~foo', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('~foo'))

        out = Writer(StringIO())
        out.write('foo~bar ~ baz', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo~bar ~ baz'))

    def test_clean(self):
        out = Writer(StringIO())
        out.write('foo: $bar|baz,quux', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

        out = Writer(StringIO())
        out.write('~foo', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '~foo')

        out = Writer(StringIO())
        out.write('foo~bar ~ baz', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo~bar ~ baz')


class TestWriteLiteral(TestCase):
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


class TestWriteShellLiteral(TestCase):
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


class TestWriteJbos(TestCase):
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


class TestWritePath(PathTestCase):
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


class TestWriteInvalid(TestCase):
    def test_invalid_type(self):
        out = Writer(StringIO())
        with self.assertRaises(TypeError):
            out.write(my_safe_str(), Syntax.target)

    def test_invalid_escape(self):
        out = Writer(StringIO())
        with self.assertRaises(ValueError):
            out.write('foo\nbar', Syntax.target)


class TestMakefile(TestCase):
    def setUp(self):
        self.makefile = Makefile('build.bfg')

    def test_variable(self):
        var = self.makefile.variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.makefile._write_variable(out, var, 'value')
        self.assertEqual(out.stream.getvalue(), 'name := value\n')

        # Test duplicate variables.
        var = self.makefile.variable('name', 'value2', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        self.assertRaises(ValueError, self.makefile.variable, 'name', 'value')
        self.assertRaises(ValueError, self.makefile.target_variable, 'name',
                          'value')
        self.assertRaises(ValueError, self.makefile.define, 'name', 'value')

    def test_target_variable(self):
        var = self.makefile.target_variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = Writer(StringIO())
        self.makefile._write_variable(out, var, 'value', target=Pattern('%'))
        self.assertEqual(out.stream.getvalue(), '%: name := value\n')

        # Test duplicate variables.
        var = self.makefile.target_variable('name', 'value2', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        self.assertRaises(ValueError, self.makefile.variable, 'name', 'value')
        self.assertRaises(ValueError, self.makefile.target_variable, 'name',
                          'value')
        self.assertRaises(ValueError, self.makefile.define, 'name', 'value')

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

        # Test duplicate variables.
        self.assertRaises(ValueError, self.makefile.variable, 'name', 'value')
        self.assertRaises(ValueError, self.makefile.target_variable, 'name',
                          'value')
        self.assertRaises(ValueError, self.makefile.define, 'name', 'value')

    def test_cmd_var(self):
        class MockCommand(object):
            command_var = 'cmd'
            command = ['command']

        var = self.makefile.cmd_var(MockCommand())
        self.assertEqual(var, Variable('CMD'))
        out = Writer(StringIO())
        self.makefile._write_variable(out, var, ['command'])
        self.assertEqual(out.stream.getvalue(), 'CMD := command\n')

    def test_rule(self):
        self.makefile.rule('target', variables={'name': 'value'},
                           recipe=['cmd'])
        out = Writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         'target: name := value\n'
                         'target:\n'
                         '\tcmd\n\n')

        self.makefile.rule('silent-target', recipe=[Silent('cmd')], phony=True)
        out = Writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         '.PHONY: silent-target\n'
                         'silent-target:\n'
                         '\t@cmd\n\n')

        self.makefile.rule('call-target', recipe=Call('fn', '1', '2'))
        out = Writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         'call-target: ; $(call fn,1,2)\n\n')

        self.makefile.rule('empty-target')
        out = Writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         'empty-target:\n\n')

        # Test duplicate targets.
        self.assertRaises(ValueError, self.makefile.rule, 'target')
        self.assertRaises(ValueError, self.makefile.rule,
                          ['target', 'target2'])
        self.assertRaises(ValueError, self.makefile.rule,
                          File(path.Path('target', path.Root.builddir)))

        # Test no targets.
        self.assertRaises(ValueError, self.makefile.rule, [])

    def test_write(self):
        out = StringIO()
        self.makefile.write(out)
        base_makefile = out.getvalue()

        out = StringIO()
        self.makefile.variable('var', 'foo')
        self.makefile.target_variable('tvar', 'bar')
        self.makefile.define('dvar', 'baz')
        self.makefile.rule('target', recipe=['cmd'])
        self.makefile.include('inc1')
        self.makefile.include('inc2', optional=True)
        self.makefile.write(out)

        self.assertEqual(
            out.getvalue(),
            base_makefile +
            'var := foo\n\n'
            '%: tvar := bar\n\n'
            'define dvar\n'
            'baz\n'
            'endef\n\n'
            'target:\n'
            '\tcmd\n\n'
            'include inc1\n'
            '-include inc2\n'
        )
