from .common import BuiltinTest

from bfg9000 import file_types
from bfg9000.builtins import command  # noqa
from bfg9000.path import Path, Root


class TestBaseCommand(BuiltinTest):
    def assertCommand(self, step, cmds, inputs=[], env={}, phony=True):
        self.assertEqual(step.cmds, cmds)
        self.assertEqual(step.inputs, inputs)
        self.assertEqual(step.env, env)
        self.assertEqual(step.phony, phony)


class TestCommand(TestBaseCommand):
    def test_single_cmd(self):
        result = self.builtin_dict['command']('foo', cmd=['echo', 'foo'])
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, [['echo', 'foo']])

    def test_string_cmd(self):
        result = self.builtin_dict['command']('foo', cmd='echo foo')
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, ['echo foo'])

    def test_file_cmd(self):
        script = self.builtin_dict['source_file']('script.py')
        result = self.builtin_dict['command']('foo', cmd=script)
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [])

    def test_file_cmd_list(self):
        script = self.builtin_dict['source_file']('script.py')
        result = self.builtin_dict['command']('foo', cmd=[script, '--foo'])
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, [
            self.env.tool('python')(script) + ['--foo']
        ], [])

    def test_file_cmd_deps(self):
        script = self.builtin_dict['source_file']('script.py')
        script.creator = 'foo'

        result = self.builtin_dict['command']('foo', cmd=script)
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, [
            self.env.tool('python')(script)
        ], [script])

    def test_multiple_cmds(self):
        result = self.builtin_dict['command']('foo', cmds=[
            ['echo', 'foo'],
            ['touch', 'bar']
        ])
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
        self.assertCommand(result.creator, [['echo', 'foo'], ['touch', 'bar']])

    def test_env(self):
        result = self.builtin_dict['command']('foo', cmd=['echo', 'foo'],
                                              environment={'NAME': 'value'})
        self.assertSame(result, file_types.Phony('foo'), exclude={'creator'})
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
        self.assertSame(result, expected, exclude={'creator'})
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
            self.assertSame(i, j, exclude={'creator'})
            self.assertCommand(i.creator, [['bison', 'hello.y']], phony=False)

    def test_file_cmd(self):
        foolex = self.builtin_dict['source_file']('foo.lex')
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', foolex
        ])
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')
        self.assertSame(result, expected, exclude={'creator'})
        self.assertCommand(result.creator, [['lex', foolex]], [], phony=False)

    def test_always_outdated(self):
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', 'foo.lex'
        ], always_outdated=True)
        expected = file_types.SourceFile(Path('lex.yy.c', Root.builddir), 'c')
        self.assertSame(result, expected, exclude={'creator'})
        self.assertCommand(result.creator, [['lex', 'foo.lex']], phony=True)

    def test_type(self):
        result = self.builtin_dict['build_step']('lex.yy.c', cmd=[
            'lex', 'foo.lex'
        ], type=self.builtin_dict['generic_file'])
        expected = file_types.File(Path('lex.yy.c', Root.builddir))
        self.assertSame(result, expected, exclude={'creator'})
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
            self.assertSame(i, j, exclude={'creator'})
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
            self.assertSame(i, j, exclude={'creator'})
            self.assertCommand(i.creator, [['bison', 'hello.y']], phony=False)

    def test_invalid_type(self):
        self.assertRaises(ValueError, self.builtin_dict['build_step'],
                          'lex.yy.c', cmd=['lex', 'foo.lex'], type=lambda x: x)

    def test_cmd_and_cmds(self):
        self.assertRaises(ValueError, self.builtin_dict['build_step'], 'foo',
                          cmd='echo foo', cmds=['echo bar'])
