from .common import BuiltinTest

from bfg9000.builtins import dist, file_types, regenerate  # noqa
from bfg9000.path import Path, Root
from bfg9000.file_types import File, Directory


class TestExtraDist(BuiltinTest):
    def test_file(self):
        self.context['extra_dist'](files='file')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file', Root.srcdir)),
        ])

    def test_multiple_files(self):
        self.context['extra_dist'](files=['file1', 'file2'])
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file1', Root.srcdir)),
            File(Path('file2', Root.srcdir)),
        ])

    def test_dir(self):
        self.context['extra_dist'](dirs='dir')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            Directory(Path('dir', Root.srcdir)),
        ])

    def test_multiple_dirs(self):
        self.context['extra_dist'](dirs=['dir1', 'dir2'])
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            Directory(Path('dir1', Root.srcdir)),
            Directory(Path('dir2', Root.srcdir)),
        ])

    def test_both(self):
        self.context['extra_dist']('file', 'dir')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('file', Root.srcdir)),
            Directory(Path('dir', Root.srcdir)),
        ])

    def test_submodule(self):
        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            self.context['extra_dist'](files='file')
        self.assertEqual(list(self.build.sources()), [
            File(Path('build.bfg', Root.srcdir)),
            File(Path('dir/file', Root.srcdir)),
        ])
