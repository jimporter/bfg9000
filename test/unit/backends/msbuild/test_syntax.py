from io import BytesIO
from lxml import etree
from lxml.builder import E

from . import *

from bfg9000.backends.msbuild.syntax import *
from bfg9000.file_types import SourceFile, StaticLibrary
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
        p3 = Path('/foo', Root.absolute)

        self.assertEqual(textify(p1), '$(OutDir)foo')
        self.assertEqual(textify(p1, quoted=True), '"$(OutDir)foo"')
        self.assertEqual(textify(p2), '$(SourceDir)foo')
        self.assertEqual(textify(p2, quoted=True), '"$(SourceDir)foo"')
        self.assertEqual(textify(p3), r'\foo')
        self.assertEqual(textify(p3, quoted=True), r'\foo')

        self.assertEqual(textify(p1, builddir=BuildDir.intermediate),
                         '$(IntDir)foo')
        self.assertEqual(textify(p2, builddir=BuildDir.intermediate),
                         '$(SourceDir)foo')
        self.assertEqual(textify(p1, builddir=BuildDir.solution),
                         '$(SolutionDir)foo')
        self.assertEqual(textify(p2, builddir=BuildDir.solution),
                         '$(SourceDir)foo')

    def test_path_spaces(self):
        p1 = Path('foo bar')
        p2 = Path('foo bar', Root.srcdir)
        p3 = Path('/foo bar', Root.absolute)

        self.assertEqual(textify(p1), '$(OutDir)foo bar')
        self.assertEqual(textify(p1, quoted=True), '"$(OutDir)foo bar"')
        self.assertEqual(textify(p2), '$(SourceDir)foo bar')
        self.assertEqual(textify(p2, quoted=True), '"$(SourceDir)foo bar"')
        self.assertEqual(textify(p3), r'\foo bar')
        self.assertEqual(textify(p3, quoted=True), r'"\foo bar"')

    def test_file(self):
        class MockCreator:
            def __init__(self, msbuild_output=False):
                self.msbuild_output = msbuild_output

        src = SourceFile(Path('foo'), 'c++')
        self.assertEqual(textify(src), '$(SolutionDir)foo')

        src.creator = MockCreator()
        self.assertEqual(textify(src), '$(IntDir)foo')

        src.creator = MockCreator(True)
        self.assertEqual(textify(src), '$(OutDir)foo')

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
    def _write_get_tree(self, proj):
        out = BytesIO()
        proj.write(out)
        return etree.fromstring(out.getvalue())

    def test_write(self):
        proj = VcxProject(FakeEnv(), 'project', output_file=Path('output'),
                          files=[{'name': SourceFile(Path('src.cpp'), 'c++'),
                                  'options': {}}])

        project = self.xpath(self._write_get_tree(proj), '/x:Project')[0]
        self.assertXPath(project, './x:PropertyGroup/x:TargetPath/text()',
                         ['$(OutDir)output'])
        self.assertXPath(project, './x:ItemGroup/x:ClCompile/@Include',
                         ['$(SolutionDir)src.cpp'])

    def test_resources(self):
        proj = VcxProject(FakeEnv(), 'project', output_file=Path('output'),
                          files=[{'name': SourceFile(Path('res.rc'), 'rc'),
                                  'options': {}}])

        project = self.xpath(self._write_get_tree(proj), '/x:Project')[0]
        self.assertXPath(project, './x:ItemGroup/x:ResourceCompile/@Include',
                         ['$(SolutionDir)res.rc'])

    def test_objs(self):
        proj = VcxProject(FakeEnv(), 'project', output_file=Path('output'),
                          objs=[StaticLibrary(Path('file.lib'), 'coff')])

        project = self.xpath(self._write_get_tree(proj), '/x:Project')[0]
        self.assertXPath(project, './x:ItemGroup/x:Link/@Include',
                         ['$(SolutionDir)file.lib'])

    def test_duplicate_basename(self):
        proj = VcxProject(
            FakeEnv(), 'project', output_file=Path('output'), files=[
                {'name': SourceFile(Path('a/src.cpp'), 'c++'), 'options': {}},
                {'name': SourceFile(Path('b/src.cpp'), 'c++'), 'options': {}},
            ])

        tree = self._write_get_tree(proj)
        self.assertXPath(tree, 'x:ItemGroup/x:ClCompile/@Include', [
            r'$(SolutionDir)a\src.cpp', r'$(SolutionDir)b\src.cpp'
        ])
        self.assertXPath(
            tree, 'x:ItemGroup/x:ClCompile/x:ObjectFileName/text()',
            [r'$(IntDir)a\src.obj', r'$(IntDir)b\src.obj']
        )

    def test_compile_options(self):
        proj = VcxProject(FakeEnv(), 'project')

        root = E.Element()
        proj._cl_compile_options(root, {})
        self.assertXPath(root, './*', [])

        root = E.Element()
        proj._cl_compile_options(root, {
            'warnings': {'level': 'all', 'as_error': True}
        })
        self.assertXPath(root, './WarningLevel/text()', ['EnableAllWarnings'])
        self.assertXPath(root, './TreatWarningAsError/text()', ['true'])

        root = E.Element()
        proj._cl_compile_options(root, {'debug': 'pdb'})
        self.assertXPath(root, './DebugInformationFormat/text()',
                         ['ProgramDatabase'])

        root = E.Element()
        proj._cl_compile_options(root, {'includes': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalIncludeDirectories/text()',
                         ['foo;bar;%(AdditionalIncludeDirectories)'])

        root = E.Element()
        proj._cl_compile_options(root, {'defines': ['foo', 'bar']})
        self.assertXPath(root, './PreprocessorDefinitions/text()',
                         ['foo;bar;%(PreprocessorDefinitions)'])

        root = E.Element()
        proj._cl_compile_options(root, {'pch': {'create': 'foo'}})
        self.assertXPath(root, './PrecompiledHeader/text()', ['Create'])
        self.assertXPath(root, './PrecompiledHeaderFile/text()', ['foo'])

        root = E.Element()
        proj._cl_compile_options(root, {'pch': {'use': 'foo'}})
        self.assertXPath(root, './PrecompiledHeader/text()', ['Use'])
        self.assertXPath(root, './PrecompiledHeaderFile/text()', ['foo'])

        root = E.Element()
        proj._cl_compile_options(root, {'runtime': 'dynamic-debug'})
        self.assertXPath(root, './RuntimeLibrary/text()',
                         ['MultiThreadedDebugDLL'])

        root = E.Element()
        proj._cl_compile_options(root, {'extra': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalOptions/text()',
                         ['foo bar %(AdditionalOptions)'])

    def test_link_options(self):
        proj = VcxProject(FakeEnv(), 'project')

        root = E.Element()
        proj._link_options(root, {})
        self.assertXPath(root, './OutputFile/text()', ['$(TargetPath)'])

        root = E.Element()
        proj._link_options(root, {'debug': True})
        self.assertXPath(root, './GenerateDebugInformation/text()', ['true'])

        root = E.Element()
        proj._link_options(root, {'import_lib': 'foo'})
        self.assertXPath(root, './ImportLibrary/text()', ['foo'])

        root = E.Element()
        proj._link_options(root, {'extra': ['foo', 'bar']})
        self.assertXPath(root, './AdditionalOptions/text()',
                         ['foo bar %(AdditionalOptions)'])

        root = E.Element()
        proj._link_options(root, {'libs': ['foo', 'bar']})
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
            [Command(None, 'rule', command=('var', 'command')), 'bar']
        ), 'command bar')
