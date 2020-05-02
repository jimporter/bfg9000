from .. import *

from bfg9000.path import Root
from bfg9000.safe_str import jbos
from bfg9000.shell import convert_args

base_dirs = {
    Root.srcdir: '$(srcdir)',
    Root.builddir: None,
}


class TestConvertArgs(PathTestCase):
    def test_string(self):
        self.assertEqual(convert_args(['foo', 'bar']), ['foo', 'bar'])

    def test_path(self):
        self.assertEqual(convert_args([self.Path('/foo')]),
                         [self.ospath.sep + 'foo'])
        self.assertEqual(convert_args([self.Path('foo')], base_dirs), ['foo'])
        self.assertEqual(convert_args([self.Path('foo', Root.srcdir)],
                                      base_dirs),
                         [self.ospath.join('$(srcdir)', 'foo')])

        self.assertRaises(TypeError, convert_args, [self.Path('foo')])

    def test_jbos(self):
        self.assertEqual(convert_args([jbos('foo', 'bar')]), ['foobar'])
        self.assertEqual(convert_args([jbos('foo', self.Path('/bar'))]),
                         ['foo' + self.ospath.sep + 'bar'])
