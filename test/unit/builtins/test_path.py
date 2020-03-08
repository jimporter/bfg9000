from .common import BuiltinTest
from bfg9000.builtins import path
from bfg9000.path import Path, Root, InstallRoot


class TestPath(BuiltinTest):
    def test_path_objects(self):
        self.assertIs(self.context['Path'], Path)
        self.assertIs(self.context['Root'], Root)
        self.assertIs(self.context['InstallRoot'], InstallRoot)

    def test_relpath(self):
        src = Path('foo/bar', Root.srcdir)
        build = Path('foo/bar')

        self.assertIs(self.context['relpath'](src), src)
        self.assertIs(self.context['relpath'](src, True), src)
        self.assertIs(self.context['relpath'](build), build)
        self.assertRaises(ValueError, self.context['relpath'], build, True)

        self.assertEqual(self.context['relpath']('foo/bar'), src)
        self.assertEqual(self.context['relpath']('foo/bar', True), src)

        with self.context.push_path(Path('foo/build.bfg', Root.srcdir)):
            self.assertIs(self.context['relpath'](src), src)
            self.assertIs(self.context['relpath'](src, True), src)
            self.assertIs(self.context['relpath'](build), build)
            self.assertRaises(ValueError, self.context['relpath'], build, True)

            self.assertEqual(self.context['relpath']('bar'), src)
            self.assertEqual(self.context['relpath']('bar', True), src)

    def test_relname(self):
        self.assertEqual(path.relname(self.context, 'foo'), 'foo')
        self.assertEqual(path.relname(self.context, ['foo', 'bar']),
                         ['foo', 'bar'])

        with self.context.push_path(Path('dir/build.bfg', Root.srcdir)):
            self.assertEqual(path.relname(self.context, 'foo'), 'dir/foo')
            self.assertEqual(path.relname(self.context, ['foo', 'bar']),
                             ['dir/foo', 'dir/bar'])

    def test_buildpath(self):
        src = Path('foo/bar', Root.srcdir)
        build = Path('foo/bar')

        self.assertIs(path.buildpath(self.context, src), src)
        self.assertRaises(ValueError, path.buildpath, self.context, src, True)
        self.assertIs(path.buildpath(self.context, build), build)
        self.assertIs(path.buildpath(self.context, build, True), build)

        self.assertEqual(path.buildpath(self.context, 'foo/bar'), build)
        self.assertEqual(path.buildpath(self.context, 'foo/bar', True), build)

        with self.context.push_path(Path('foo/build.bfg', Root.srcdir)):
            self.assertIs(path.buildpath(self.context, src), src)
            self.assertRaises(ValueError, path.buildpath, self.context, src,
                              True)
            self.assertIs(path.buildpath(self.context, build), build)
            self.assertIs(path.buildpath(self.context, build, True), build)

            self.assertEqual(path.buildpath(self.context, 'bar'), build)
            self.assertEqual(path.buildpath(self.context, 'bar', True), build)

    def test_within_directory(self):
        within = path.within_directory
        directory = Path('dir', Root.srcdir)
        subdir = Path('dir/sub', Root.srcdir)

        self.assertEqual(within(Path('foo', Root.srcdir), directory),
                         Path('dir/foo', Root.srcdir))
        self.assertEqual(within(Path('foo/bar', Root.srcdir), directory),
                         Path('dir/foo/bar', Root.srcdir))
        self.assertEqual(within(Path('dir/foo', Root.srcdir), directory),
                         Path('dir/dir/foo', Root.srcdir))

        self.assertEqual(within(Path('foo', Root.srcdir), subdir),
                         Path('dir/sub/PAR/foo', Root.srcdir))
        self.assertEqual(within(Path('foo/bar', Root.srcdir), subdir),
                         Path('dir/sub/PAR/foo/bar', Root.srcdir))
        self.assertEqual(within(Path('dir/foo', Root.srcdir), subdir),
                         Path('dir/sub/foo', Root.srcdir))
        self.assertEqual(within(Path('dir/foo/bar', Root.srcdir), subdir),
                         Path('dir/sub/foo/bar', Root.srcdir))
        self.assertEqual(within(Path('dir/sub/foo', Root.srcdir), subdir),
                         Path('dir/sub/sub/foo', Root.srcdir))
