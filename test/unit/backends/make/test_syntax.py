from io import StringIO

from ... import *

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.make.syntax import *
from bfg9000.backends.make.syntax import syntax_string
from bfg9000.file_types import File
from bfg9000.platforms.host import platform_info

esc_colon = ':' if platform_info().family == 'windows' else '\\:'


def quoted(s):
    return "'" + s + "'"


class my_safe_str(safe_str.safe_string):
    pass


class TestWriteString(TestCase):
    def make_writer(self):
        return Writer(StringIO(), {})

    def test_target(self):
        out = self.make_writer()
        out.write('foo: $bar|baz,quux', Syntax.target)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

        out = self.make_writer()
        out.write('~foo', Syntax.target)
        self.assertEqual(out.stream.getvalue(), '\\~foo')

        out = self.make_writer()
        out.write('foo~bar ~ baz', Syntax.target)
        self.assertEqual(out.stream.getvalue(), 'foo~bar\\ ~\\ baz')

    def test_dependency(self):
        out = self.make_writer()
        out.write('foo: $bar|baz,quux', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

        out = self.make_writer()
        out.write('~foo', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '\\~foo')

        out = self.make_writer()
        out.write('foo~bar ~ baz', Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), 'foo~bar\\ ~\\ baz')

    def test_function(self):
        out = self.make_writer()
        out.write('foo: $bar|baz,quux', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz$,quux'))

        out = self.make_writer()
        out.write('~foo', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('~foo'))

        out = self.make_writer()
        out.write('foo~bar ~ baz', Syntax.function)
        self.assertEqual(out.stream.getvalue(), quoted('foo~bar ~ baz'))

    def test_shell(self):
        out = self.make_writer()
        out.write('foo: $bar|baz,quux', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo: $$bar|baz,quux'))

        out = self.make_writer()
        out.write('~foo', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('~foo'))

        out = self.make_writer()
        out.write('foo~bar ~ baz', Syntax.shell)
        self.assertEqual(out.stream.getvalue(), quoted('foo~bar ~ baz'))

    def test_clean(self):
        out = self.make_writer()
        out.write('foo: $bar|baz,quux', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo: $$bar|baz,quux')

        out = self.make_writer()
        out.write('~foo', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '~foo')

        out = self.make_writer()
        out.write('foo~bar ~ baz', Syntax.clean)
        self.assertEqual(out.stream.getvalue(), 'foo~bar ~ baz')


class TestWriteLiteral(TestCase):
    def setUp(self):
        self.out = Writer(StringIO(), {})

    def test_target(self):
        self.out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.target)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_dependency(self):
        self.out.write(safe_str.literal('foo: $bar|baz,quux'),
                       Syntax.dependency)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_function(self):
        self.out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.function)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_shell(self):
        self.out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.shell)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $bar|baz,quux')

    def test_clean(self):
        self.out.write(safe_str.literal('foo: $bar|baz,quux'), Syntax.clean)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $bar|baz,quux')


class TestWriteShellLiteral(TestCase):
    def setUp(self):
        self.out = Writer(StringIO(), {})

    def test_target(self):
        self.out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                       Syntax.target)
        self.assertEqual(self.out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar|baz,quux')

    def test_dependency(self):
        self.out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                       Syntax.dependency)
        self.assertEqual(self.out.stream.getvalue(),
                         'foo' + esc_colon + '\\ $$bar\\|baz,quux')

    def test_function(self):
        self.out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                       Syntax.function)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $$bar|baz$,quux')

    def test_shell(self):
        self.out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                       Syntax.shell)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $$bar|baz,quux')

    def test_clean(self):
        self.out.write(safe_str.shell_literal('foo: $bar|baz,quux'),
                       Syntax.clean)
        self.assertEqual(self.out.stream.getvalue(), 'foo: $$bar|baz,quux')


class TestWriteJbos(TestCase):
    def setUp(self):
        self.out = Writer(StringIO(), {})

    def test_target(self):
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        self.out.write(s, Syntax.target)
        self.assertEqual(self.out.stream.getvalue(), '$$foo$bar')

    def test_dependency(self):
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        self.out.write(s, Syntax.dependency)
        self.assertEqual(self.out.stream.getvalue(), '$$foo$bar')

    def test_function(self):
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        self.out.write(s, Syntax.function)
        self.assertEqual(self.out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_shell(self):
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        self.out.write(s, Syntax.shell)
        self.assertEqual(self.out.stream.getvalue(), quoted('$$foo') + '$bar')

    def test_clean(self):
        s = safe_str.jbos('$foo', safe_str.literal('$bar'))
        self.out.write(s, Syntax.clean)
        self.assertEqual(self.out.stream.getvalue(), '$$foo$bar')


class TestWritePath(PathTestCase):
    def setUp(self):
        self.out = Writer(StringIO(), {path.Root.srcdir: Variable('srcdir')})

    def test_target(self):
        self.out.write(self.Path('foo', path.Root.srcdir), Syntax.target)
        self.assertEqual(self.out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))

    def test_dependency(self):
        self.out.write(self.Path('foo', path.Root.srcdir), Syntax.dependency)
        self.assertEqual(self.out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))

    def test_function(self):
        self.out.write(self.Path('foo', path.Root.srcdir), Syntax.function)
        self.assertEqual(self.out.stream.getvalue(),
                         quoted(self.ospath.join('$(srcdir)', 'foo')))

    def test_shell(self):
        self.out.write(self.Path('foo', path.Root.srcdir), Syntax.shell)
        self.assertEqual(self.out.stream.getvalue(),
                         quoted(self.ospath.join('$(srcdir)', 'foo')))

    def test_clean(self):
        self.out.write(self.Path('foo', path.Root.srcdir), Syntax.clean)
        self.assertEqual(self.out.stream.getvalue(),
                         self.ospath.join('$(srcdir)', 'foo'))


class TestWriteSyntaxString(PathTestCase):
    def make_writer(self):
        return Writer(StringIO(), {})

    def test_target(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')))
        out = self.make_writer()
        out.write(fn, Syntax.target)
        self.assertEqual(out.stream.getvalue(), '$(fn 1,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')),
                           Syntax.function)
        out = self.make_writer()
        out.write(fn, Syntax.target)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')), quoted=True)
        out = self.make_writer()
        out.write(fn, Syntax.target)
        self.assertEqual(out.stream.getvalue(), "'$(fn 1,2)'")

    def test_dependency(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')))
        out = self.make_writer()
        out.write(fn, Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '$(fn 1,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')),
                           Syntax.function)
        out = self.make_writer()
        out.write(fn, Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')), quoted=True)
        out = self.make_writer()
        out.write(fn, Syntax.dependency)
        self.assertEqual(out.stream.getvalue(), "'$(fn 1,2)'")

    def test_function(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')))
        out = self.make_writer()
        out.write(fn, Syntax.function)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')),
                           Syntax.function)
        out = self.make_writer()
        out.write(fn, Syntax.function)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')), quoted=True)
        out = self.make_writer()
        out.write(fn, Syntax.function)
        self.assertEqual(out.stream.getvalue(), "'$(fn 1$,2)'")

    def test_shell(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')))
        out = self.make_writer()
        out.write(fn, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(fn 1,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')),
                           Syntax.function)
        out = self.make_writer()
        out.write(fn, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')), quoted=True)
        out = self.make_writer()
        out.write(fn, Syntax.shell)
        self.assertEqual(out.stream.getvalue(), "'$(fn 1,2)'")

    def test_clean(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')))
        out = self.make_writer()
        out.write(fn, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$(fn 1,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')),
                           Syntax.function)
        out = self.make_writer()
        out.write(fn, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), '$(fn 1$,2)')

        fn = syntax_string(jbos(lit('$(fn '), '1,2', lit(')')), quoted=True)
        out = self.make_writer()
        out.write(fn, Syntax.clean)
        self.assertEqual(out.stream.getvalue(), "'$(fn 1,2)'")


class TestWriteInvalid(TestCase):
    def setUp(self):
        self.out = Writer(StringIO(), {})

    def test_invalid_type(self):
        with self.assertRaises(TypeError):
            self.out.write(my_safe_str(), Syntax.target)

    def test_invalid_escape(self):
        with self.assertRaises(ValueError):
            self.out.write('foo\nbar', Syntax.target)


class TestPattern(TestCase):
    def test_equality(self):
        self.assertTrue(Pattern('%.c') == Pattern('%.c'))
        self.assertFalse(Pattern('%.c') != Pattern('%.c'))

        self.assertFalse(Pattern('%.c') == Pattern('%.h'))
        self.assertTrue(Pattern('%.c') != Pattern('%.h'))

        self.assertTrue(Pattern('%\\%.c') == Pattern('%\\%.c'))
        self.assertFalse(Pattern('%\\%.c') != Pattern('%\\%.c'))

    def test_use(self):
        self.assertEqual(Pattern('%.c').use(),
                         safe_str.jbos(safe_str.literal('%'), '.c'))

    def test_write(self):
        out = Writer(StringIO(), {})
        out.write(Pattern('%.c'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '%.c')

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

    def test_use(self):
        self.assertEqual(Variable('foo').use(),
                         safe_str.literal('$(foo)'))

    def test_write(self):
        out = Writer(StringIO(), {})
        out.write(Variable('foo'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(foo)')

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
    def make_writer(self):
        return Writer(StringIO(), {})

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

    def test_use(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        self.assertEqual(Function('fn').use(), syntax_string(
            jbos(lit('$(fn)')), Syntax.function
        ))
        self.assertEqual(Function('fn', '1', '2').use(), syntax_string(
            jbos(lit('$(fn '), '1', lit(','), '2', lit(')')), Syntax.function
        ))
        self.assertEqual(
            Function('fn', ['a', 'b'], ['1', '2']).use(),
            syntax_string(jbos(lit('$(fn '), 'a', lit(' '), 'b', lit(','), '1',
                               lit(' '), '2', lit(')')), Syntax.function)
        )

    def test_write(self):
        out = self.make_writer()
        out.write(Function('fn'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(fn)')

        out = self.make_writer()
        out.write(Function('fn', '1', '2'), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(fn 1,2)')

        out = self.make_writer()
        out.write(Function('fn', ['a', 'b'], ['1', '2']), Syntax.shell)
        self.assertEqual(out.stream.getvalue(), '$(fn a b,1 2)')

    def test_concat_str(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1', lit(','), '2', lit(')')),
                           Syntax.function)
        self.assertEqual(Function('fn', '1', '2') + 'foo', jbos(fn, 'foo'))
        self.assertEqual('foo' + Function('fn', '1', '2'), jbos('foo', fn))

        fn = syntax_string(jbos(lit('$(fn '), '1', lit(','), '2', lit(')')),
                           Syntax.function, True)
        self.assertEqual(Function('fn', '1', '2', quoted=True) + 'foo',
                         jbos(fn, 'foo'))
        self.assertEqual('foo' + Function('fn', '1', '2', quoted=True),
                         jbos('foo', fn))

    def test_concat_path(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        fn = syntax_string(jbos(lit('$(fn '), '1', lit(','), '2', lit(')')),
                           Syntax.function)
        self.assertEqual(Function('fn', '1', '2') + path.Path('foo'),
                         jbos(fn, path.Path('foo')))
        self.assertEqual(path.Path('foo') + Function('fn', '1', '2'),
                         jbos(path.Path('foo'), fn))

        fn = syntax_string(jbos(lit('$(fn '), '1', lit(','), '2', lit(')')),
                           Syntax.function, True)
        self.assertEqual((Function('fn', '1', '2', quoted=True) +
                          path.Path('foo')),
                         jbos(fn, path.Path('foo')))
        self.assertEqual((path.Path('foo') +
                          Function('fn', '1', '2', quoted=True)),
                         jbos(path.Path('foo'), fn))

    def test_concat_var(self):
        jbos, lit = safe_str.jbos, safe_str.literal

        foo = syntax_string(jbos(lit('$(foo '), '1', lit(','), '2', lit(')')),
                            Syntax.function)
        bar = syntax_string(jbos(lit('$(bar '), '3', lit(','), '4', lit(')')),
                            Syntax.function)
        self.assertEqual(Function('foo', '1', '2') + Function('bar', '3', '4'),
                         jbos(foo, bar))

        foo = syntax_string(jbos(lit('$(foo '), '1', lit(','), '2', lit(')')),
                            Syntax.function, True)
        self.assertEqual((Function('foo', '1', '2', quoted=True) +
                          Function('bar', '3', '4')),
                         jbos(foo, bar))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            Function('fn', kwarg=True)


class TestSilent(TestCase):
    def test_silent(self):
        v = Variable('foo')
        self.assertIs(Silent(v).data, v)


class TestMakefile(TestCase):
    def setUp(self):
        self.makefile = Makefile('build.bfg')

    def test_destdir(self):
        out = self.makefile.writer(StringIO())
        self.makefile._write_variable(
            out, Variable('name'),
            path.Path('foo', path.InstallRoot.bindir, destdir=True)
        )
        self.assertEqual(out.stream.getvalue(), 'name := {}\n'.format(
            quoted(os.path.join('$(bindir)', 'foo'))
        ))

        makefile = Makefile('build.bfg', destdir=True)
        out = makefile.writer(StringIO())
        makefile._write_variable(
            out, Variable('name'),
            path.Path('foo', path.InstallRoot.bindir, destdir=True)
        )
        self.assertEqual(out.stream.getvalue(), 'name := {}\n'.format(
            quoted(os.path.join('$(DESTDIR)$(bindir)', 'foo'))
        ))

    def test_variable(self):
        var = self.makefile.variable('name', 'value')
        self.assertEqual(var, Variable('name'))
        out = self.makefile.writer(StringIO())
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
        out = self.makefile.writer(StringIO())
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
        out = self.makefile.writer(StringIO())
        self.makefile._write_define(out, *self.makefile._defines[0])
        self.assertEqual(out.stream.getvalue(),
                         'define name\nvalue\nendef\n\n')

        var = self.makefile.define('name', 'value', exist_ok=True)
        self.assertEqual(var, Variable('name'))

        var = self.makefile.define('multi', ['value1', 'value2'])
        self.assertEqual(var, Variable('multi'))
        out = self.makefile.writer(StringIO())
        self.makefile._write_define(out, *self.makefile._defines[1])
        self.assertEqual(out.stream.getvalue(),
                         'define multi\nvalue1\nvalue2\nendef\n\n')

        # Test duplicate variables.
        self.assertRaises(ValueError, self.makefile.variable, 'name', 'value')
        self.assertRaises(ValueError, self.makefile.target_variable, 'name',
                          'value')
        self.assertRaises(ValueError, self.makefile.define, 'name', 'value')

    def test_cmd_var(self):
        class MockCommand:
            command_var = 'cmd'
            command = ['command']

        var = self.makefile.cmd_var(MockCommand())
        self.assertEqual(var, Variable('CMD'))
        out = self.makefile.writer(StringIO())
        self.makefile._write_variable(out, var, ['command'])
        self.assertEqual(out.stream.getvalue(), 'CMD := command\n')

    def test_rule(self):
        self.makefile.rule('target', variables={'name': 'value'},
                           recipe=['cmd'])
        out = self.makefile.writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         'target: name := value\n'
                         'target:\n'
                         '\tcmd\n\n')

        self.makefile.rule('silent-target', recipe=[Silent('cmd')], phony=True)
        out = self.makefile.writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         '.PHONY: silent-target\n'
                         'silent-target:\n'
                         '\t@cmd\n\n')

        self.makefile.rule('call-target', recipe=Call('fn', '1', '2'))
        out = self.makefile.writer(StringIO())
        self.makefile._write_rule(out, self.makefile._rules[-1])
        self.assertEqual(out.stream.getvalue(),
                         'call-target: ; $(call fn,1,2)\n\n')

        self.makefile.rule('empty-target')
        out = self.makefile.writer(StringIO())
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
