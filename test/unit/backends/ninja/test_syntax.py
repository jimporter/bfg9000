from io import StringIO

from ... import *

from bfg9000 import path
from bfg9000 import safe_str
from bfg9000.backends.ninja.syntax import *
from bfg9000.file_types import File
from bfg9000.platforms.host import platform_info

quote_char = '"' if platform_info().family == 'windows' else "'"


def quoted(s):
    return quote_char + s + quote_char


class my_safe_str(safe_str.safe_string):
    pass


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


class TestWriteString(TestCase):
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


class TestWriteLiteral(TestCase):
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


class TestWriteShellLiteral(TestCase):
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


class TestWriteJbos(TestCase):
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


class TestWritePath(PathTestCase):
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


class TestWriteInvalid(TestCase):
    def test_invalid_type(self):
        out = Writer(StringIO())
        with self.assertRaises(TypeError):
            out.write(my_safe_str(), Syntax.output)

    def test_invalid_escape(self):
        out = Writer(StringIO())
        with self.assertRaises(ValueError):
            out.write('foo\nbar', Syntax.output)


class TestNinjaFile(TestCase):
    def setUp(self):
        self.ninjafile = NinjaFile('build.bfg')

    def test_min_version(self):
        self.assertIs(self.ninjafile._min_version, None)

        self.ninjafile.min_version('1.0')
        self.assertEqual(str(self.ninjafile._min_version), '1.0')
        self.ninjafile.min_version('1.1')
        self.assertEqual(str(self.ninjafile._min_version), '1.1')
        self.ninjafile.min_version('1.0')
        self.assertEqual(str(self.ninjafile._min_version), '1.1')

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

    def test_cmd_var(self):
        class MockCommand(object):
            command_var = 'cmd'
            command = ['command']

        var = self.ninjafile.cmd_var(MockCommand())
        self.assertEqual(var, Variable('cmd'))
        out = Writer(StringIO())
        self.ninjafile._write_variable(out, var, ['command'])
        self.assertEqual(out.stream.getvalue(), 'cmd = command\n')

    def test_rule(self):
        self.ninjafile.rule('my_rule', ['cmd'])
        out = Writer(StringIO())
        self.ninjafile._write_rule(out, 'my_rule',
                                   self.ninjafile._rules['my_rule'])
        self.assertEqual(out.stream.getvalue(),
                         'rule my_rule\n'
                         '  command = cmd\n')

        self.ninjafile.rule('deps_rule', ['cmd'], depfile='out.d', deps='gcc')
        out = Writer(StringIO())
        self.ninjafile._write_rule(out, 'deps_rule',
                                   self.ninjafile._rules['deps_rule'])
        self.assertEqual(out.stream.getvalue(),
                         'rule deps_rule\n'
                         '  command = cmd\n'
                         '  depfile = out.d\n'
                         '  deps = gcc\n')

        self.ninjafile.rule('misc_rule', ['cmd'], description='desc',
                            generator=True, pool='console', restat=True)
        out = Writer(StringIO())
        self.ninjafile._write_rule(out, 'misc_rule',
                                   self.ninjafile._rules['misc_rule'])
        self.assertEqual(out.stream.getvalue(),
                         'rule misc_rule\n'
                         '  command = cmd\n'
                         '  description = desc\n'
                         '  generator = 1\n'
                         '  pool = console\n'
                         '  restat = 1\n')

        # Test duplicate rules.
        self.assertRaises(ValueError, self.ninjafile.rule, 'my_rule', ['cmd'])

        # Test invalid args.
        self.assertRaises(ValueError, self.ninjafile.rule, 'my_rule!', ['cmd'])
        self.assertRaises(ValueError, self.ninjafile.rule, 'pool_rule',
                          ['cmd'], pool='pool')

    def test_build(self):
        self.ninjafile.rule('my_rule', ['cmd'])

        self.ninjafile.build('output', 'my_rule')
        out = Writer(StringIO())
        self.ninjafile._write_build(out, self.ninjafile._builds[-1])
        self.assertEqual(out.stream.getvalue(), 'build output: my_rule\n')

        self.ninjafile.build('doutput', 'my_rule', inputs='input',
                             implicit='implicit', order_only='order')
        out = Writer(StringIO())
        self.ninjafile._write_build(out, self.ninjafile._builds[-1])
        self.assertEqual(out.stream.getvalue(),
                         'build doutput: my_rule input | implicit || order\n')

        self.ninjafile.build('voutput', 'my_rule', variables={'var': 'value'})
        out = Writer(StringIO())
        self.ninjafile._write_build(out, self.ninjafile._builds[-1])
        self.assertEqual(out.stream.getvalue(),
                         'build voutput: my_rule\n'
                         '  var = value\n')

        # Test duplicate targets.
        self.assertRaises(ValueError, self.ninjafile.build, 'output',
                          'my_rule')
        self.assertRaises(ValueError, self.ninjafile.build,
                          ['output', 'output2'], 'my_rule')
        self.assertRaises(ValueError, self.ninjafile.build,
                          File(path.Path('output', path.Root.builddir)),
                          'my_rule')

        # Test unknown rule.
        self.assertRaises(ValueError, self.ninjafile.build, 'output2',
                          'unknown_rule')

    def test_write(self):
        out = StringIO()
        self.ninjafile.write(out)
        base_ninjafile = out.getvalue()

        out = StringIO()
        self.ninjafile.variable('var', 'foo')
        self.ninjafile.rule('my_rule', ['cmd'], pool='console')
        self.ninjafile.build('output', 'my_rule')
        self.ninjafile.default('output')
        self.ninjafile.write(out)

        self.assertEqual(
            out.getvalue(),
            base_ninjafile +
            'ninja_required_version = 1.5\n\n'
            'var = foo\n\n'
            'rule my_rule\n'
            '  command = cmd\n'
            '  pool = console\n\n'
            'build output: my_rule\n\n'
            'default output\n'
        )
