from collections import OrderedDict

from .. import *

from bfg9000.path import Path
from bfg9000.shell import windows
from bfg9000.safe_str import jbos, literal, shell_literal
from bfg9000.shell.list import shell_list


class TestSplit(TestCase):
    def test_single(self):
        self.assertEqual(windows.split('foo'), ['foo'])
        self.assertEqual(windows.split(' foo'), ['foo'])
        self.assertEqual(windows.split('foo '), ['foo'])
        self.assertEqual(windows.split(' foo '), ['foo'])

    def test_multiple(self):
        self.assertEqual(windows.split('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_backslash(self):
        self.assertEqual(windows.split(r'C:\path\to\file'),
                         [r'C:\path\to\file'])

    def test_quote(self):
        self.assertEqual(windows.split('foo "bar baz"'), ['foo', 'bar baz'])
        self.assertEqual(windows.split('foo"bar baz"'), ['foobar baz'])
        self.assertEqual(windows.split(r'foo "c:\path\\"'),
                         ['foo', 'c:\\path\\'])
        self.assertEqual(windows.split('foo "it\'s \\"good\\""'),
                         ['foo', 'it\'s "good"'])

    def test_type(self):
        self.assertEqual(windows.split('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))

    def test_invalid(self):
        self.assertRaises(TypeError, windows.split, 1)


class TestJoin(TestCase):
    def test_empty(self):
        self.assertEqual(windows.join([]), '')

    def test_single(self):
        self.assertEqual(windows.join(['foo']), 'foo')
        self.assertEqual(windows.join(['foo bar']), '"foo bar"')

    def test_multiple(self):
        self.assertEqual(windows.join(['foo bar', 'baz']), '"foo bar" baz')

    def test_literal(self):
        self.assertEqual(windows.join(['foo bar', shell_literal('>'), 'baz']),
                         '"foo bar" > baz')
        self.assertEqual(windows.join(['foo bar' + shell_literal('>'), 'baz']),
                         '"foo bar"> baz')


class TestListify(TestCase):
    def test_string(self):
        self.assertEqual(windows.listify('foo bar baz'), ['foo', 'bar', 'baz'])

    def test_list(self):
        self.assertEqual(windows.listify(['foo bar', 'baz']),
                         ['foo bar', 'baz'])

    def test_type(self):
        self.assertEqual(windows.listify('foo bar baz', type=tuple),
                         ('foo', 'bar', 'baz'))
        self.assertEqual(windows.listify(['foo bar', 'baz'], type=tuple),
                         ('foo bar', 'baz'))


class TestQuote(TestCase):
    def assertQuote(self, original, needs_quote, inner_quoted, quoted,
                    **kwargs):
        self.assertEqual(windows.inner_quote(original, **kwargs), inner_quoted)
        self.assertEqual(windows.inner_quote_info(original, **kwargs),
                         (inner_quoted, needs_quote))

        self.assertEqual(windows.quote(original, **kwargs), quoted)
        self.assertEqual(windows.quote_info(original, **kwargs),
                         (quoted, needs_quote))
        self.assertEqual(windows.force_quote(original, **kwargs),
                         windows.wrap_quotes(inner_quoted))

    def test_empty(self):
        self.assertQuote('', True, '', '""')

    def test_simple(self):
        self.assertQuote('foo', False, 'foo', 'foo')

    def test_space(self):
        self.assertQuote('foo bar', True, 'foo bar', '"foo bar"')

    def test_quote(self):
        self.assertQuote('"foo"', True, r'\"foo\"', r'"\"foo\""')
        self.assertQuote('"foo"z', True, r'\"foo\"z', r'"\"foo\"z"')
        self.assertQuote('a"foo"', True, r'a\"foo\"', r'"a\"foo\""')
        self.assertQuote('a"foo"z', True, r'a\"foo\"z', r'"a\"foo\"z"')

    def test_escaped_quote(self):
        self.assertQuote(r'\"foobar', True, r'\\\"foobar', r'"\\\"foobar"')
        self.assertQuote(r'foo\"bar', True, r'foo\\\"bar', r'"foo\\\"bar"')
        self.assertQuote(r'foobar\"', True, r'foobar\\\"', r'"foobar\\\""')

    def test_backslash(self):
        self.assertQuote(r'foo\bar', False, r'foo\bar', r'foo\bar')
        self.assertQuote('foo\\bar\\', True, r'foo\bar\\', r'"foo\bar\\"')

    def test_escape_percent(self):
        self.assertQuote(r'100%', False, r'100%', r'100%')
        self.assertQuote(r'100%', False, r'100%%', r'100%%',
                         escape_percent=True)
        self.assertQuote(r'"100%"', True, r'\"100%\"', r'"\"100%\""')
        self.assertQuote(r'"100%"', True, r'\"100%%\"', r'"\"100%%\""',
                         escape_percent=True)

    def test_shell_chars(self):
        self.assertQuote('&&', True, '&&', '"&&"')
        self.assertQuote('>', True, '>', '">"')
        self.assertQuote('|', True, '|', '"|"')

    def test_literal(self):
        self.assertQuote(shell_literal('>'), False, '>', '>')
        self.assertQuote(shell_literal(''), False, '', '')

        s = shell_literal('>') + 'foo bar'
        self.assertEqual(windows.quote(s), '>"foo bar"')
        self.assertEqual(windows.quote_info(s), ('>"foo bar"', True))

    def test_invalid(self):
        for fn in (windows.quote, windows.quote_info, windows.inner_quote,
                   windows.inner_quote_info):
            with self.assertRaises(TypeError):
                fn(1)


class TestWrapQuotes(TestCase):
    def test_simple(self):
        self.assertEqual(windows.wrap_quotes(''), '""')
        self.assertEqual(windows.wrap_quotes('f'), '"f"')
        self.assertEqual(windows.wrap_quotes('fo'), '"fo"')
        self.assertEqual(windows.wrap_quotes('foo'), '"foo"')

    def test_escaped_quote(self):
        self.assertEqual(windows.wrap_quotes(r'\"'), r'"\""')
        self.assertEqual(windows.wrap_quotes(r'\"foobar'), r'"\"foobar"')
        self.assertEqual(windows.wrap_quotes(r'foo\"bar'), r'"foo\"bar"')
        self.assertEqual(windows.wrap_quotes(r'foobar\"'), r'"foobar\""')


class TestEscapeLine(TestCase):
    def test_string(self):
        self.assertEqual(windows.escape_line('foo bar'),
                         shell_list([shell_literal('foo bar')]))

    def test_jbos(self):
        self.assertEqual(
            windows.escape_line(jbos('foo', literal('bar'))),
            shell_list([ jbos(shell_literal('foo'), literal('bar')) ])
        )

    def test_path(self):
        self.assertEqual(windows.escape_line(Path('foo')),
                         shell_list([Path('foo')]))

    def test_iterable(self):
        self.assertEqual(windows.escape_line(['foo', 'bar']), ['foo', 'bar'])
        gen = (i for i in ['foo', 'bar'])
        self.assertEqual(windows.escape_line(gen), gen)
        self.assertEqual(windows.escape_line(gen, listify=True),
                         ['foo', 'bar'])


class TestJoinLines(TestCase):
    def test_empty(self):
        self.assertEqual(windows.join_lines([]), [])

    def test_single(self):
        self.assertEqual(windows.join_lines(['foo']), shell_list([
            shell_literal('foo')
        ]))
        self.assertEqual(windows.join_lines([['foo']]), ['foo'])
        self.assertEqual(windows.join_lines([['foo', 'bar']]), ['foo', 'bar'])

    def test_multiple(self):
        self.assertEqual(windows.join_lines(['foo', 'bar']), shell_list([
            shell_literal('foo'),
            shell_literal('&&'),
            shell_literal('bar'),
        ]))
        self.assertEqual(
            windows.join_lines([['foo', 'bar'], 'baz']),
            shell_list([
                'foo', 'bar',
                shell_literal('&&'),
                shell_literal('baz'),
            ])
        )


class TestGlobalEnv(TestCase):
    def test_empty(self):
        self.assertEqual(windows.global_env({}), [])
        self.assertEqual(windows.global_env({}, ['cmd']), shell_list([
            shell_literal('cmd')
        ]))
        self.assertEqual(windows.global_env({}, [['cmd']]), ['cmd'])

    def test_single(self):
        env = {'NAME': 'VALUE'}
        self.assertEqual(windows.global_env(env), shell_list([
            'set', 'NAME=VALUE'
        ]))

        self.assertEqual(windows.global_env(env, ['cmd']), shell_list([
            'set', 'NAME=VALUE',
            shell_literal('&&'),
            shell_literal('cmd')
        ]))

        self.assertEqual(windows.global_env(env, [['cmd']]), shell_list([
            'set', 'NAME=VALUE',
            shell_literal('&&'),
            'cmd'
        ]))

    def test_multiple(self):
        env = OrderedDict((('FOO', 'oof'), ('BAR', 'rab')))
        self.assertEqual(windows.global_env(env), shell_list([
            'set', 'FOO=oof',
            shell_literal('&&'),
            'set', 'BAR=rab'
        ]))

        self.assertEqual(windows.global_env(env, ['cmd']), shell_list([
            'set', 'FOO=oof',
            shell_literal('&&'),
            'set', 'BAR=rab',
            shell_literal('&&'),
            shell_literal('cmd')
        ]))

        self.assertEqual(windows.global_env(env, [['cmd']]), shell_list([
            'set', 'FOO=oof',
            shell_literal('&&'),
            'set', 'BAR=rab',
            shell_literal('&&'),
            'cmd'
        ]))
