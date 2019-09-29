from lxml import etree
from six import BytesIO

from . import *

from bfg9000.backends.msbuild.syntax import *
from bfg9000.file_types import SourceFile


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
