from . import *

from bfg9000 import file_types
from bfg9000.build_inputs import BuildInputs, Edge
from bfg9000.iterutils import default_sentinel, listify
from bfg9000.path import Path, Root


class TestEdge(TestCase):
    def setUp(self):
        self.env = make_env()
        self.build = BuildInputs(self.env, Path('build.bfg'))

    def assertEdge(self, edge, raw_output, output=default_sentinel,
                   public_output=default_sentinel, extra_deps=[],
                   description=None):
        if output is default_sentinel:
            output = listify(raw_output)
        if public_output is default_sentinel:
            public_output = raw_output

        self.assertEqual(edge.raw_output, raw_output)
        self.assertEqual(edge.output, output)
        self.assertEqual(edge.public_output, public_output)
        self.assertEqual(edge.extra_deps, extra_deps)
        self.assertEqual(edge.description, description)

    def test_simple(self):
        output = file_types.File(Path('file.txt'))
        self.assertEdge(Edge(self.build, output), output)

    def test_multiple_outputs(self):
        output = [file_types.File(Path('foo.txt')),
                  file_types.File(Path('bar.txt'))]
        self.assertEdge(Edge(self.build, output), output)

    def test_final_output(self):
        output = file_types.File(Path('file.txt'))
        final = file_types.File(Path('final.txt'))
        self.assertEdge(Edge(self.build, output, final),
                        output, public_output=final)

    def test_private_outputs(self):
        output = [file_types.File(Path('foo.txt')),
                  file_types.File(Path('bar.txt'))]
        output[1].private = True

        self.assertEdge(Edge(self.build, output),
                        output, public_output=output[0])

    def test_extra_deps(self):
        dep = file_types.File(Path('dep.txt', Root.srcdir))
        dep2 = file_types.File(Path('dep.txt', Root.builddir))
        output = file_types.File(Path('file.txt'))

        self.assertEdge(Edge(self.build, output, extra_deps=dep),
                        output, extra_deps=[dep])
        self.assertEdge(Edge(self.build, output, extra_deps=dep2),
                        output, extra_deps=[dep2])
        self.assertEdge(Edge(self.build, output, extra_deps=dep.path),
                        output, extra_deps=[dep])
        self.assertEdge(Edge(self.build, output, extra_deps=dep2.path),
                        output, extra_deps=[dep2])
        self.assertEdge(Edge(self.build, output, extra_deps='dep.txt'),
                        output, extra_deps=[dep])

    def test_description(self):
        output = file_types.File(Path('file.txt'))
        self.assertEdge(Edge(self.build, output, description='desc'),
                        output, description='desc')
