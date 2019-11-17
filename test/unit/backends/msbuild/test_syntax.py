from lxml import etree
from six import BytesIO

from . import *

from bfg9000.backends.msbuild.syntax import *
from bfg9000.file_types import SourceFile
from bfg9000.path import Path, Root
from bfg9000.safe_str import jbos, literal, safe_string


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

    def test_convert_attr(self):
        self.assertEqual(CommandProject.convert_attr('foo'), 'foo')
        self.assertEqual(CommandProject.convert_attr(['foo', 'bar']),
                         'foo;bar')
