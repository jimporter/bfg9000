from lxml import etree
from lxml.builder import E
from six import BytesIO

from . import *

from bfg9000.backends.msbuild.syntax import *
from bfg9000.file_types import SourceFile
from bfg9000.path import Path, Root
from bfg9000.safe_str import jbos, literal, safe_string
from bfg9000.tools.common import Command


class my_safe_str(safe_string):
    pass


class TestTextify(TestCase):
    def test_string(self):
        self.assertEqual(textify('foo'), 'foo')
        self.assertEqual(textify('foo', True), 'foo')
        self.assertEqual(textify('foo bar'), 'foo bar')
        self.assertEqual(textify('foo bar', True), '"foo bar"')

    def test_literal(self):
        self.assertEqual(textify(literal('foo bar')), 'foo bar')
        self.assertEqual(textify(literal('foo bar'), True), 'foo bar')

    def test_jbos(self):
        j = jbos('foo', literal('='), 'bar baz')
        self.assertEqual(textify(j), 'foo=bar baz')
        self.assertEqual(textify(j, True), 'foo="bar baz"')

    def test_path(self):
        p1 = Path('foo')
        p2 = Path('foo', Root.srcdir)

        self.assertEqual(textify(p1), r'$(OutDir)\foo')
        self.assertEqual(textify(p2), r'$(SourceDir)\foo')

        self.assertEqual(textify(p1, builddir=BuildDir.intermediate),
                         r'$(IntDir)\foo')
        self.assertEqual(textify(p2, builddir=BuildDir.intermediate),
                         r'$(SourceDir)\foo')
        self.assertEqual(textify(p1, builddir=BuildDir.solution),
                         r'$(SolutionDir)\foo')
        self.assertEqual(textify(p2, builddir=BuildDir.solution),
                         r'$(SourceDir)\foo')

    def test_file(self):
        class MockCreator(object):
            def __init__(self, msbuild_output=False):
                self.msbuild_output = msbuild_output

        src = SourceFile(Path('foo'), 'c++')
        self.assertEqual(textify(src), r'$(SolutionDir)\foo')

        src.creator = MockCreator()
        self.assertEqual(textify(src), r'$(IntDir)\foo')

        src.creator = MockCreator(True)
        self.assertEqual(textify(src), r'$(OutDir)\foo')

    def test_invalid(self):
        with self.assertRaises(TypeError):
            textify(my_safe_str())


class ProjectTest(TestCase):
    xmlns = 'http://schemas.microsoft.com/developer/msbuild/2003'

    def xpath(self, node, query):
        return node.xpath(query, namespaces={'x': self.xmlns})

    def assertXPath(self, node, query, result):
        self.assertEqual(self.xpath(node, query), result)


class TestVcxProject(ProjectTest):
    def test_write(self):
        proj = VcxProject(FakeEnv(), 'project', output_file=Path('output'),
                          files=[{'name': SourceFile(Path('src.cpp'), 'c++'),
                                  'options': {}}])
        out = BytesIO()
        proj.write(out)
        tree = etree.fromstring(out.getvalue())
        project = self.xpath(tree, '/x:Project')[0]
        self.assertXPath(project, './x:PropertyGroup/x:TargetPath/text()',
                         [r'$(OutDir)\output'])
        self.assertXPath(project, './x:ItemGroup/x:ClCompile/@Include',
                         [r'$(SolutionDir)\src.cpp'])

    def test_duplicate_basename(self):
        proj = VcxProject(
            FakeEnv(), 'project', output_file=Path('output'), files=[
                {'name': SourceFile(Path('a/src.cpp'), 'c++'), 'options': {}},
                {'name': SourceFile(Path('b/src.cpp'), 'c++'), 'options': {}},
            ])
        out = BytesIO()
        proj.write(out)
        tree = etree.fromstring(out.getvalue())
        self.assertXPath(tree, 'x:ItemGroup/x:ClCompile/@Include', [
            r'$(SolutionDir)\a\src.cpp', r'$(SolutionDir)\b\src.cpp'
        ])
        self.assertXPath(
            tree, 'x:ItemGroup/x:ClCompile/x:ObjectFileName/text()',
            [r'$(IntDir)\a\src.obj', r'$(IntDir)\b\src.obj']
        )

    def test_compile_options(self):
        proj = VcxProject(FakeEnv(), 'project')

        root = E.Element()
        proj._write_compile_options(root, {})
        self.assertXPath(root, './*', [])

        root = E.Element()
        proj._write_compile_options(root, {
            'warnings': {'level': 'all', 'as_error': True}
        })
        self.assertXPath(root, './WarningLevel/text()', ['EnableAllWarnings'])
        self.assertXPath(root, './TreatWarningAsError/text()', ['true'])

        root = E.Element()
        proj._write_compile_options(root, {'includes': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalIncludeDirectories/text()',
                         ['foo;bar;%(AdditionalIncludeDirectories)'])

        root = E.Element()
        proj._write_compile_options(root, {'defines': ['foo', 'bar']})
        self.assertXPath(root, './PreprocessorDefinitions/text()',
                         ['foo;bar;%(PreprocessorDefinitions)'])

        root = E.Element()
        proj._write_compile_options(root, {'pch': {'create': 'foo'}})
        self.assertXPath(root, './PrecompiledHeader/text()', ['Create'])
        self.assertXPath(root, './PrecompiledHeaderFile/text()', ['foo'])

        root = E.Element()
        proj._write_compile_options(root, {'pch': {'use': 'foo'}})
        self.assertXPath(root, './PrecompiledHeader/text()', ['Use'])
        self.assertXPath(root, './PrecompiledHeaderFile/text()', ['foo'])

        root = E.Element()
        proj._write_compile_options(root, {'extra': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalOptions/text()',
                         ['foo bar %(AdditionalOptions)'])

    def test_link_options(self):
        proj = VcxProject(FakeEnv(), 'project')

        root = E.Element()
        proj._write_link_options(root, {})
        self.assertXPath(root, './OutputFile/text()', ['$(TargetPath)'])

        root = E.Element()
        proj._write_link_options(root, {'import_lib': 'foo'})
        self.assertXPath(root, './ImportLibrary/text()', ['foo'])

        root = E.Element()
        proj._write_link_options(root, {'extra': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalOptions/text()',
                         ['foo bar %(AdditionalOptions)'])

        root = E.Element()
        proj._write_link_options(root, {'libs': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalDependencies/text()',
                         ['foo;bar;%(AdditionalDependencies)'])


class TestNoopProject(ProjectTest):
    def test_write(self):
        proj = NoopProject(FakeEnv(), 'project')
        out = BytesIO()
        proj.write(out)
        tree = etree.fromstring(out.getvalue())
        self.assertXPath(tree, '/x:Project/x:Target/@Name', ['Build'])


class TestCommandProject(ProjectTest):
    def test_write(self):
        proj = CommandProject(FakeEnv(), 'project', commands=[
            CommandProject.task('Exec', Command='echo foo')
        ])
        out = BytesIO()
        proj.write(out)
        tree = etree.fromstring(out.getvalue())
        build = self.xpath(tree, '/x:Project/x:Target[@Name="Build"]')[0]
        self.assertXPath(build, './x:MakeDir/@Directories', ['$(OutDir)'])
        self.assertXPath(build, './x:Exec/@Command', ['echo foo'])

        # Now try without makedir.
        proj = CommandProject(FakeEnv(), 'project', commands=[
            CommandProject.task('Exec', Command='echo foo')
        ], makedir=False)
        out = BytesIO()
        proj.write(out)
        tree = etree.fromstring(out.getvalue())
        build = self.xpath(tree, '/x:Project/x:Target[@Name="Build"]')[0]
        self.assertXPath(build, './x:MakeDir', [])
        self.assertXPath(build, './x:Exec/@Command', ['echo foo'])

    def test_convert_attr(self):
        self.assertEqual(CommandProject.convert_attr('foo'), 'foo')
        self.assertEqual(CommandProject.convert_attr(['foo', 'bar']),
                         'foo;bar')

    def test_convert_command(self):
        self.assertEqual(CommandProject.convert_command(['foo', 'bar']),
                         'foo bar')
        self.assertEqual(CommandProject.convert_command(
            [Command(None, 'rule', 'var', 'command'), 'bar']
        ), 'command bar')
