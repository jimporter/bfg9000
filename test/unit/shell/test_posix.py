import mock
from collections import OrderedDict

from .. import *

from bfg9000.path import Path
from bfg9000.safe_str import jbos, literal, shell_literal
from bfg9000.shell import posix
from bfg9000.shell.list import shell_list


class TestSplit(TestCase):
    def test_single(self):
        self.assertEqual(posix.split('foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(posix.split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(posix.split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(posix.split('foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(posix.split('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_invalid(self):
        self.assertRaises(TypeError, posix.split, 1)


class TestJoin(TestCase):
    def test_empty(self):
        self.assertEqual(posix.join([]), '')

    def test_single(self):
        self.assertEqual(posix.join(['foo']), 'foo')
        self.assertEqual(posix.join(['foo bar']), "'foo bar'")

    def test_multiple(self):
        self.assertEqual(posix.join(['foo bar', 'baz']), "'foo bar' baz")


class TestListify(TestCase):
    def test_string(self):
        self.assertEqual(posix.listify('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_list(self):
        self.assertEqual(posix.listify(['foo bar', 'baz']), ['foo bar', 'baz'])

    def test_type(self):
        self.assertEqual(posix.listify('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))
        self.assertEqual(posix.listify(['foo bar', 'baz'], type=tuple),
                         ('foo bar', 'baz'))


class TestQuote(TestCase):
    def assertQuote(self, original, needs_quote, inner_quoted, quoted):
        self.assertEqual(posix.inner_quote(original), inner_quoted)
        self.assertEqual(posix.inner_quote_info(original),
                         (inner_quoted, needs_quote))

        self.assertEqual(posix.quote(original), quoted)
        self.assertEqual(posix.quote_info(original), (quoted, needs_quote))

    def test_empty(self):
        self.assertQuote('', False, '', '')

    def test_simple(self):
        self.assertQuote('foo', False, 'foo', 'foo')

    def test_space(self):
        self.assertQuote('foo bar', True, 'foo bar', "'foo bar'")

    def test_quote(self):
        self.assertQuote('"foo"', True, r'"foo"', "'\"foo\"'")
        self.assertQuote("'foo'", True, r"'\''foo'\''", r"\''foo'\'")
        self.assertQuote("'foo'z", True, r"'\''foo'\''z", r"\''foo'\''z'")
        self.assertQuote("a'foo'", True, r"a'\''foo'\''", r"'a'\''foo'\'")
        self.assertQuote("a'foo'z", True, r"a'\''foo'\''z", r"'a'\''foo'\''z'")

    def test_escaped_quote(self):
        self.assertQuote(r"\'foobar", True, r"\'\''foobar", r"'\'\''foobar'")
        self.assertQuote(r"foo\'bar", True, r"foo\'\''bar", r"'foo\'\''bar'")
        self.assertQuote(r"foobar\'", True, r"foobar\'\''", r"'foobar\'\'")

    def test_shell_chars(self):
        self.assertQuote('&&', True, '&&', "'&&'")
        self.assertQuote('>', True, '>', "'>'")
        self.assertQuote('|', True, '|', "'|'")


class TestWrapQuotes(TestCase):
    def test_simple(self):
        self.assertEqual(posix.wrap_quotes(''), "''")
        self.assertEqual(posix.wrap_quotes('f'), "'f'")
        self.assertEqual(posix.wrap_quotes('fo'), "'fo'")
        self.assertEqual(posix.wrap_quotes('foo'), "'foo'")

    def test_escaped_quote(self):
        self.assertEqual(posix.wrap_quotes(r"'\''"), r"\'")
        self.assertEqual(posix.wrap_quotes(r"'\''foobar"), r"\''foobar'")
        self.assertEqual(posix.wrap_quotes(r"foo'\''bar"), r"'foo'\''bar'")
        self.assertEqual(posix.wrap_quotes(r"foobar'\''"), r"'foobar'\'")


class TestEscapeLine(TestCase):
    class FakePlatform(object):
        def __init__(self, family):
            self.family = family

    def test_string(self):
        self.assertEqual(posix.escape_line('foobar'),
                         shell_list([shell_literal(r'foobar')]))

        with mock.patch('bfg9000.shell.posix.platform_info',
                        return_value=self.FakePlatform('posix')):
            self.assertEqual(posix.escape_line(r'foo\bar'),
                             shell_list([shell_literal(r'foo\bar')]))

        with mock.patch('bfg9000.shell.posix.platform_info',
                        return_value=self.FakePlatform('windows')):
            self.assertEqual(posix.escape_line(r'foo\bar'),
                             shell_list([shell_literal(r'foo\\bar')]))

    def test_jbos(self):
        self.assertEqual(
            posix.escape_line(jbos('foo', literal('bar'))),
            shell_list([ jbos(shell_literal('foo'), literal('bar')) ])
        )

        s = jbos(r'foo\bar', literal(r'baz\quux'))
        with mock.patch('bfg9000.shell.posix.platform_info',
                        return_value=self.FakePlatform('posix')):
            self.assertEqual(posix.escape_line(s), shell_list([jbos(
                shell_literal(r'foo\bar'), literal(r'baz\quux')
            )]))

        with mock.patch('bfg9000.shell.posix.platform_info',
                        return_value=self.FakePlatform('windows')):
            self.assertEqual(posix.escape_line(s), shell_list([jbos(
                shell_literal(r'foo\\bar'), literal(r'baz\quux')
            )]))

    def test_path(self):
        self.assertEqual(posix.escape_line(Path('foo')),
                         shell_list([Path('foo')]))

    def test_iterable(self):
        self.assertEqual(posix.escape_line(['foo', 'bar']), ['foo', 'bar'])
        gen = (i for i in ['foo', 'bar'])
        self.assertEqual(posix.escape_line(gen), gen)
        self.assertEqual(posix.escape_line(gen, listify=True), ['foo', 'bar'])


class TestJoinLines(TestCase):
    def test_empty(self):
        self.assertEqual(posix.join_lines([]), [])

    def test_single(self):
        self.assertEqual(posix.join_lines(['foo']), shell_list([
            shell_literal('foo')
        ]))
        self.assertEqual(posix.join_lines([['foo']]), ['foo'])
        self.assertEqual(posix.join_lines([['foo', 'bar']]), ['foo', 'bar'])

    def test_multiple(self):
        self.assertEqual(posix.join_lines(['foo', 'bar']), shell_list([
            shell_literal('foo'),
            shell_literal('&&'),
            shell_literal('bar'),
        ]))
        self.assertEqual(
            posix.join_lines([['foo', 'bar'], 'baz']),
            shell_list([
                'foo', 'bar',
                shell_literal('&&'),
                shell_literal('baz'),
            ])
        )


class TestLocalEnv(TestCase):
    def test_empty(self):
        self.assertEqual(posix.local_env({}, 'cmd'), shell_list([
            shell_literal('cmd')
        ]))
        self.assertEqual(posix.local_env({}, ['cmd']), ['cmd'])

    def test_single(self):
        env = {'NAME': 'VALUE'}
        self.assertEqual(posix.local_env(env, 'cmd'), shell_list([
            jbos('NAME', shell_literal('='), 'VALUE'),
            shell_literal('cmd')
        ]))

        self.assertEqual(posix.local_env(env, ['cmd']), shell_list([
            jbos('NAME', shell_literal('='), 'VALUE'),
            'cmd'
        ]))

    def test_multiple(self):
        env = OrderedDict((('FOO', 'oof'), ('BAR', 'rab')))
        self.assertEqual(posix.local_env(env, 'cmd'), shell_list([
            jbos('FOO', shell_literal('='), 'oof'),
            jbos('BAR', shell_literal('='), 'rab'),
            shell_literal('cmd')
        ]))

        self.assertEqual(posix.local_env(env, ['cmd']), shell_list([
            jbos('FOO', shell_literal('='), 'oof'),
            jbos('BAR', shell_literal('='), 'rab'),
            'cmd'
        ]))


class TestGlobalEnv(TestCase):
    def test_empty(self):
        self.assertEqual(posix.global_env({}), [])
        self.assertEqual(posix.global_env({}, ['cmd']), shell_list([
            shell_literal('cmd')
        ]))
        self.assertEqual(posix.global_env({}, [['cmd']]), ['cmd'])

    def test_single(self):
        env = {'NAME': 'VALUE'}
        self.assertEqual(posix.global_env(env), shell_list([
            'export', jbos('NAME', shell_literal('='), 'VALUE')
        ]))

        self.assertEqual(posix.global_env(env, ['cmd']), shell_list([
            'export', jbos('NAME', shell_literal('='), 'VALUE'),
            shell_literal('&&'),
            shell_literal('cmd')
        ]))

        self.assertEqual(posix.global_env(env, [['cmd']]), shell_list([
            'export', jbos('NAME', shell_literal('='), 'VALUE'),
            shell_literal('&&'),
            'cmd'
        ]))

    def test_multiple(self):
        env = OrderedDict((('FOO', 'oof'), ('BAR', 'rab')))
        self.assertEqual(posix.global_env(env), shell_list([
            'export', jbos('FOO', shell_literal('='), 'oof'),
            shell_literal('&&'),
            'export', jbos('BAR', shell_literal('='), 'rab')
        ]))

        self.assertEqual(posix.global_env(env, ['cmd']), shell_list([
            'export', jbos('FOO', shell_literal('='), 'oof'),
            shell_literal('&&'),
            'export', jbos('BAR', shell_literal('='), 'rab'),
            shell_literal('&&'),
            shell_literal('cmd')
        ]))

        self.assertEqual(posix.global_env(env, [['cmd']]), shell_list([
            'export', jbos('FOO', shell_literal('='), 'oof'),
            shell_literal('&&'),
            'export', jbos('BAR', shell_literal('='), 'rab'),
            shell_literal('&&'),
            'cmd'
        ]))
