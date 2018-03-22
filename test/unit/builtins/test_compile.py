import unittest
from collections import namedtuple

from bfg9000.builtins import builtin, compile
from bfg9000 import file_types
from bfg9000.build_inputs import BuildInputs
from bfg9000.environment import Environment
from bfg9000.path import Path, Root

MockCompile = namedtuple('MockCompile', ['file'])


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.env = Environment(None, None, None, None, None, {},
                               (False, False), None)
        self.build = BuildInputs(self.env, Path('build.bfg', Root.srcdir))
        self.builtin_dict = builtin.bind(build_inputs=self.build, env=self.env)


class TestObjectFile(BaseTest):
    def test_identity(self):
        obj = file_types.ObjectFile(Path('object', Root.srcdir), None)
        result = compile.object_file(None, self.build, self.env, obj)
        self.assertEqual(result, obj)

    def test_src_file(self):
        result = compile.object_file(None, self.build, self.env, 'object')
        self.assertEqual(result, file_types.ObjectFile(
            Path('object', Root.srcdir), None
        ))

    def test_expects_name_or_file(self):
        self.assertRaises(TypeError, compile.object_file, None, self.build,
                          self.env)


class TestPrecompiledHeader(BaseTest):
    def test_identity(self):
        obj = file_types.PrecompiledHeader(Path('header', Root.srcdir), None)
        result = compile.precompiled_header(None, self.build, self.env, obj)
        self.assertEqual(result, obj)

    def test_src_file(self):
        result = compile.precompiled_header(None, self.build, self.env,
                                            'header')
        self.assertEqual(result, file_types.PrecompiledHeader(
            Path('header', Root.srcdir), None
        ))

    def test_expects_name_or_file(self):
        self.assertRaises(TypeError, compile.precompiled_header, None,
                          self.build, self.env)


class TestObjectFiles(BaseTest):
    def make_object_files(self, make_src=False):
        files = [file_types.ObjectFile(Path(i, Root.srcdir), None)
                 for i in ['obj1', 'obj2']]
        if make_src:
            src_files = [file_types.SourceFile(Path(i, Root.srcdir), None)
                         for i in ['src1', 'src2']]
            for f, s in zip(files, src_files):
                f.creator = MockCompile(s)

        obj_files = compile.object_files(self.builtin_dict, self.build,
                                         self.env, files)

        if make_src:
            return obj_files, files, src_files
        return obj_files, files

    def test_initialize(self):
        obj_files, files = self.make_object_files()
        self.assertEqual(list(obj_files), files)

    def test_getitem_index(self):
        obj_files, files = self.make_object_files()
        self.assertEqual(obj_files[0], files[0])

    def test_getitem_string(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files['src1'], files[0])

    def test_getitem_path(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files[src_files[0].path], files[0])

    def test_getitem_file(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertEqual(obj_files[src_files[0]], files[0])

    def test_getitem_not_found(self):
        obj_files, files, src_files = self.make_object_files(True)
        self.assertRaises(IndexError, lambda: obj_files[2])
        self.assertRaises(IndexError, lambda: obj_files['src3'])
        self.assertRaises(IndexError, lambda: obj_files[Path(
            'src3', Root.srcdir
        )])
