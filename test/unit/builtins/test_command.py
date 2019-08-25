from .common import AttrDict, BuiltinTest, TestCase

from bfg9000 import file_types
from bfg9000.builtins.command import Placeholder
from bfg9000.path import Path, Root
from bfg9000.safe_str import literal, jbos


class TestBaseCommand(BuiltinTest):
    def assertCommand(self, step, cmds, files=[], extra_deps=[], env={},
                      phony=True):
        self.assertEqual(step.cmds, cmds)
        self.assertEqual(step.files, files)
        self.assertEqual(step.extra_deps, extra_deps)
        self.assertEqual(step.env, env)
        self.assertEqual(step.phony, phony)


class TestCommand(TestBaseCommand):
    def test_single_cmd(self):
        result = self.builtin_dict['command']('foo', cmd=['echo', 'foo'])
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [['echo', 'foo']])

    def test_string_cmd(self):
        result = self.builtin_dict['command']('foo', cmd='echo foo')
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, ['echo foo'])

    def test_file_cmd(self):
        script = self.builtin_dict['source_file']('script.py')
        result = self.builtin_dict['command']('foo', cmd=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [])

    def test_file_cmd_list(self):
        script = self.builtin_dict['source_file']('script.py')
        result = self.builtin_dict['command']('foo', cmd=[script, '--foo'])
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script) + ['--foo']
        ], [])

    def test_file_cmd_deps(self):
        script = self.builtin_dict['source_file']('script.py')
        script.creator = 'foo'

        result = self.builtin_dict['command']('foo', cmd=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], extra_deps=[script])

    def test_input(self):
        script = self.builtin_dict['source_file']('script.py')

        command = self.builtin_dict['command']
        result = command('foo', cmd=[command.input], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        result = command('foo', cmd=[command.input[0]], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        result = command('foo', cmd=[command.input[0:]], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        with self.assertRaises(IndexError):
            command('foo', cmd=[command.input[1]], files=script)

    def test_input_line(self):
        script = self.builtin_dict['source_file']('script.py')

        command = self.builtin_dict['command']
        result = command('foo', cmd=command.input, files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        result = command('foo', cmd=command.input[0], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        result = command('foo', cmd=command.input[0:], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

        with self.assertRaises(IndexError):
            command('foo', cmd=command.input[1], files=script)
        with self.assertRaises(ValueError):
            command('foo', cmd=command.input, files=[script, script])

    def test_input_deps(self):
        script = self.builtin_dict['source_file']('script.py')
        script.creator = 'foo'

        command = self.builtin_dict['command']
        result = command('foo', cmd=[command.input], files=script)
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

    def test_multiple_cmds(self):
        result = self.builtin_dict['command']('foo', cmds=[
            ['echo', 'foo'],
            ['touch', 'bar']
        ])
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [['echo', 'foo'], ['touch', 'bar']])

    def test_env(self):
        result = self.builtin_dict['command']('foo', cmd=['echo', 'foo'],
                                              environment={'NAME': 'value'})
        self.assertSameFile(result, file_types.Phony('foo'))
        self.assertCommand(result.creator, [['echo', 'foo']],
                           env={'NAME': 'value'})

    def test_cmd_and_cmds(self):
        self.assertRaises(ValueError, self.builtin_dict['command'], 'foo',
                          cmd='echo foo', cmds=['echo bar'])


class TestBuildStep(TestBaseCommand):
    def test_single_output(self):
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', 'foo.lex'
        ])
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', 'foo.lex']], phony=False)

    def test_multiple_outputs(self):
        result = self.builtin_dict['build_step'](
            ['hello.tab.h', 'hello.tab.c'], cmd=['bison', 'hello.y']
        )
        expected = [
            file_types.HeaderFile(Path('hello.tab.h', Root.builddir), 'c'),
            file_types.SourceFile(Path('hello.tab.c', Root.builddir), 'c')
        ]
        for i, j in zip(result, expected):
            self.assertSameFile(i, j)
            self.assertCommand(i.creator, [['bison', 'hello.y']], phony=False)

    def test_file_cmd(self):
        foolex = self.builtin_dict['source_file']('foo.lex')
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', foolex
        ])
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', foolex]],
                           extra_deps=[foolex], phony=False)

    def test_input(self):
        foolex = self.builtin_dict['source_file']('foo.lex')
        build_step = self.builtin_dict['build_step']
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')

        result = build_step('lex.yy.c', cmd=['lex', build_step.input],
                            files=foolex)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', foolex]], [foolex],
                           phony=False)

        result = build_step('lex.yy.c', cmd=['lex', build_step.input[0]],
                            files=foolex)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', foolex]], [foolex],
                           phony=False)

        result = build_step('lex.yy.c', cmd=['lex', build_step.input[0:]],
                            files=foolex)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', foolex]], [foolex],
                           phony=False)

        with self.assertRaises(IndexError):
            build_step('foo', cmd=[build_step.input[1]], files=foolex)

    def test_input_line(self):
        foopy = self.builtin_dict['source_file']('foo.py')
        build_step = self.builtin_dict['build_step']
        expected = file_types.SourceFile(Path('foo.c', Root.builddir), 'c')

        result = build_step('foo.c', cmd=build_step.input, files=foopy)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [self.env.tool('python')(foopy)],
                           [foopy], phony=False)

        result = build_step('foo.c', cmd=build_step.input[0], files=foopy)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [self.env.tool('python')(foopy)],
                           [foopy], phony=False)

        result = build_step('foo.c', cmd=build_step.input[0:], files=foopy)
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [self.env.tool('python')(foopy)],
                           [foopy], phony=False)

        with self.assertRaises(IndexError):
            build_step('foo.c', cmd=build_step.input[1], files=foopy)
        with self.assertRaises(ValueError):
            build_step('foo.c', cmd=build_step.input, files=[foopy, foopy])

    def test_output(self):
        build_step = self.builtin_dict['build_step']
        expected = file_types.SourceFile(Path('foo-lex.c', Root.builddir), 'c')

        result = build_step('foo-lex.c', cmd=[
            'lex', 'foo.lex', '-o', build_step.output
        ])
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [[
            'lex', 'foo.lex', '-o', expected
        ]], phony=False)

        result = build_step('foo-lex.c', cmd=[
            'lex', 'foo.lex', '-o', build_step.output[0]
        ])
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [[
            'lex', 'foo.lex', '-o', expected
        ]], phony=False)

        result = build_step('foo-lex.c', cmd=[
            'lex', 'foo.lex', '-o', build_step.output[0:]
        ])
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [[
            'lex', 'foo.lex', '-o', expected
        ]], phony=False)

        with self.assertRaises(IndexError):
            build_step('foo', cmd=[build_step.output[1]])

    def test_always_outdated(self):
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', 'foo.lex'
        ], always_outdated=True)
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', 'foo.lex']], phony=True)

    def test_type(self):
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', 'foo.lex'
        ], type=self.builtin_dict['generic_file'])
        expected = file_types.File(Path('lex.yy.c', Root.builddir))
        self.assertSameFile(result, expected)
        self.assertCommand(result.creator, [['lex', 'foo.lex']], phony=False)

    def test_type_multiple_files(self):
        result = self.builtin_dict['build_step'](
            ['hello.tab.h', 'hello.tab.c'], cmd=['bison', 'hello.y'],
            type=self.builtin_dict['generic_file']
        )
        expected = [
            file_types.File(Path('hello.tab.h', Root.builddir)),
            file_types.File(Path('hello.tab.c', Root.builddir))
        ]
        for i, j in zip(result, expected):
            self.assertSameFile(i, j)
            self.assertCommand(i.creator, [['bison', 'hello.y']], phony=False)

    def test_multiple_types(self):
        result = self.builtin_dict['build_step'](
            ['hello.tab.h', 'hello.tab.c'], cmd=['bison', 'hello.y'],
            type=[self.builtin_dict['generic_file'],
                  self.builtin_dict['header_file']]
        )
        expected = [
            file_types.File(Path('hello.tab.h', Root.builddir)),
            file_types.HeaderFile(Path('hello.tab.c', Root.builddir), None)
        ]
        for i, j in zip(result, expected):
            self.assertSameFile(i, j)
            self.assertCommand(i.creator, [['bison', 'hello.y']], phony=False)

    def test_invalid_type(self):
        self.assertRaises(ValueError, self.builtin_dict['build_step'],
                          'lex.yy.c', cmd=['lex', 'foo.lex'], type=lambda x: x)

    def test_cmd_and_cmds(self):
        self.assertRaises(ValueError, self.builtin_dict['build_step'], 'foo',
                          cmd='echo foo', cmds=['echo bar'])


class TestPlaceholder(TestCase):
    def test_expand(self):
        p = Placeholder('files')
        self.assertEqual(p.expand(AttrDict(files=[])), [])
        self.assertEqual(p.expand(AttrDict(files=['foo'])), ['foo'])
        self.assertEqual(p.expand(AttrDict(files=['foo', 'bar'])),
                         ['foo', 'bar'])

    def test_expand_index(self):
        p = Placeholder('files')[0]
        with self.assertRaises(IndexError):
            p.expand(AttrDict(files=[]))
        self.assertEqual(p.expand(AttrDict(files=['foo'])), ['foo'])
        self.assertEqual(p.expand(AttrDict(files=['foo', 'bar'])), ['foo'])

    def test_expand_slice(self):
        p = Placeholder('files')[0:1]
        self.assertEqual(p.expand(AttrDict(files=[])), [])
        self.assertEqual(p.expand(AttrDict(files=['foo'])), ['foo'])
        self.assertEqual(p.expand(AttrDict(files=['foo', 'bar'])), ['foo'])

    def test_expand_word(self):
        p = Placeholder('files')
        zero = AttrDict(files=[])
        one = AttrDict(files=['foo'])
        two = AttrDict(files=['foo', 'bar'])

        self.assertEqual(Placeholder.expand_word(p, zero), [])
        self.assertEqual(Placeholder.expand_word(p, one), ['foo'])
        self.assertEqual(Placeholder.expand_word(p, two), ['foo', 'bar'])

        with self.assertRaises(IndexError):
            Placeholder.expand_word(p[0], zero)
        self.assertEqual(Placeholder.expand_word(p[0], one), ['foo'])
        self.assertEqual(Placeholder.expand_word(p[0], two), ['foo'])

        self.assertEqual(Placeholder.expand_word(p[0:1], zero), [])
        self.assertEqual(Placeholder.expand_word(p[0:1], one), ['foo'])
        self.assertEqual(Placeholder.expand_word(p[0:1], two), ['foo'])

    def test_expand_word_jbos(self):
        p = Placeholder('files')
        zero = AttrDict(files=[])
        one = AttrDict(files=[literal('foo')])
        two = AttrDict(files=[literal('foo'), literal('bar')])
        foo = jbos('{', literal('foo'), '}')
        bar = jbos('{', literal('bar'), '}')

        j = '{' + p + '}'
        self.assertEqual(Placeholder.expand_word(j, zero), [])
        self.assertEqual(Placeholder.expand_word(j, one), [foo])
        self.assertEqual(Placeholder.expand_word(j, two), [foo, bar])

        j = '{' + p[0] + '}'
        with self.assertRaises(IndexError):
            Placeholder.expand_word(j, zero)
        self.assertEqual(Placeholder.expand_word(j, one), [foo])
        self.assertEqual(Placeholder.expand_word(j, two), [foo])

        j = '{' + p[0:1] + '}'
        self.assertEqual(Placeholder.expand_word(j, zero), [])
        self.assertEqual(Placeholder.expand_word(j, one), [foo])
        self.assertEqual(Placeholder.expand_word(j, two), [foo])

        j = jbos('foo')
        self.assertEqual(Placeholder.expand_word(j, zero), [j])
        self.assertEqual(Placeholder.expand_word(j, one), [j])
        self.assertEqual(Placeholder.expand_word(j, two), [j])

        with self.assertRaises(ValueError):
            Placeholder.expand_word(p + p, zero)

    def test_expand_word_misc(self):
        self.assertEqual(Placeholder.expand_word(
            'foo', AttrDict(files=[])
        ), ['foo'])
        self.assertEqual(Placeholder.expand_word(
            'foo', AttrDict(files=['foo'])
        ), ['foo'])
        self.assertEqual(Placeholder.expand_word(
            'foo', AttrDict(files=['foo', 'bar'])
        ), ['foo'])

    def test_index_twice(self):
        p = Placeholder('files')
        self.assertRaises(TypeError, lambda: p[0][0])
        self.assertRaises(TypeError, lambda: p[0:1][0])
        self.assertRaises(TypeError, lambda: p[0][0:1])
        self.assertRaises(TypeError, lambda: p[0:1][0:1])