from .common import BuiltinTest
from bfg9000.builtins import dist, file_types, regenerate
from bfg9000.path import Path, Root
from bfg9000.file_types import File, Directory


class TestExtraDist(BuiltinTest):
    def test_file(self):
        dist.extra_dist(self.builtin_dict, files='file')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file', Root.srcdir)),
        ])

    def test_multiple_files(self):
        dist.extra_dist(self.builtin_dict, files=['file1', 'file2'])
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file1', Root.srcdir)),
            File(Path('file2', Root.srcdir)),
        ])

    def test_dir(self):
        dist.extra_dist(self.builtin_dict, dirs='dir')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            Directory(Path('dir', Root.srcdir)),
        ])

    def test_multiple_dirs(self):
        dist.extra_dist(self.builtin_dict, dirs=['dir1', 'dir2'])
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            Directory(Path('dir1', Root.srcdir)),
            Directory(Path('dir2', Root.srcdir)),
        ])

    def test_both(self):
        dist.extra_dist(self.builtin_dict, 'file', 'dir')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file', Root.srcdir)),
            Directory(Path('dir', Root.srcdir)),
        ])
