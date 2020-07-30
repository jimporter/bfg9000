from collections import namedtuple
from unittest import mock

from .common import AlwaysEqual, BuiltinTest, FileTest

from bfg9000.backends.make import syntax as make
from bfg9000.backends.ninja import syntax as ninja
from bfg9000.builtins import (compile, default, install, link,  # noqa
                              packages, project)  # noqa
from bfg9000.file_types import *
from bfg9000.path import Path, Root, InstallRoot
from bfg9000.platforms import target

MockEnv = namedtuple('MockEnv', ['target_platform'])


class TestInstall(BuiltinTest):
    def test_install_none(self):
        self.assertEqual(self.context['install'](), None)
        self.assertEqual(self.build['install'].explicit, [])
        self.assertEqual(self.build['install'].host, {})
        self.assertEqual(self.build['install'].target, {})

    def test_install_single(self):
        exe = Executable(Path('exe', Root.srcdir), None)
        host = Executable(Path('exe', InstallRoot.bindir, True), None)
        target = Executable(Path('exe', InstallRoot.bindir), None)

        self.assertEqual(self.context['install'](exe), target)
        self.assertEqual(self.build['install'].explicit, [exe])
        self.assertEqual(self.build['install'].host, {exe: host})
        self.assertEqual(self.build['install'].target, {exe: target})

    def test_install_multiple(self):
        exes = [Executable(Path('exe1', Root.srcdir), None),
                Executable(Path('exe2', Root.srcdir), None)]
        hosts = [Executable(Path('exe1', InstallRoot.bindir, True), None),
                 Executable(Path('exe2', InstallRoot.bindir, True), None)]
        targets = [Executable(Path('exe1', InstallRoot.bindir), None),
                   Executable(Path('exe2', InstallRoot.bindir), None)]

        self.assertEqual(self.context['install'](*exes), tuple(targets))
        install = self.build['install']
        self.assertEqual(install.explicit, exes)
        self.assertEqual(install.host, dict(zip(exes, hosts)))
        self.assertEqual(install.target, dict(zip(exes, targets)))

    def test_install_nested_multiple(self):
        exes = [Executable(Path('exe1', Root.srcdir), None),
                Executable(Path('exe2', Root.srcdir), None)]
        hosts = [Executable(Path('exe1', InstallRoot.bindir, True), None),
                 Executable(Path('exe2', InstallRoot.bindir, True), None)]
        targets = [Executable(Path('exe1', InstallRoot.bindir), None),
                   Executable(Path('exe2', InstallRoot.bindir), None)]

        self.assertEqual(self.context['install'](exes[0], [exes[1]], None),
                         (targets[0], [targets[1]], None))
        install = self.build['install']
        self.assertEqual(install.explicit, exes)
        self.assertEqual(install.host, dict(zip(exes, hosts)))
        self.assertEqual(install.target, dict(zip(exes, targets)))

    def test_install_add_to_default(self):
        exe = Executable(Path('exe', Root.srcdir), None)
        exe.creator = 'creator'
        host = Executable(Path('exe', InstallRoot.bindir, True), None)
        target = Executable(Path('exe', InstallRoot.bindir), None)

        self.assertEqual(self.context['install'](exe), target)
        self.assertEqual(self.build['install'].explicit, [exe])
        self.assertEqual(self.build['install'].host, {exe: host})
        self.assertEqual(self.build['install'].target, {exe: target})
        self.assertEqual(self.build['defaults'].outputs, [exe])

    def test_invalid(self):
        phony = Phony('name')
        self.assertRaises(TypeError, self.context['install'], phony)

        exe = Executable(Path('/path/to/exe', Root.absolute), None)
        self.assertRaises(ValueError, self.context['install'], exe)

    def test_cant_install(self):
        exes = [Executable(Path('exe1', Root.srcdir), None),
                Executable(Path('exe2', Root.srcdir), None)]
        targets = [Executable(Path('exe1', InstallRoot.bindir), None),
                   Executable(Path('exe2', InstallRoot.bindir), None)]
        install = self.context['install']
        with mock.patch('bfg9000.builtins.install.can_install',
                        return_value=False):
            with mock.patch('warnings.warn') as m:
                self.assertEqual(install(exes[0]), targets[0])
                self.assertEqual(m.call_count, 1)
            with mock.patch('warnings.warn') as m:
                self.assertEqual(install(*exes), tuple(targets))
                self.assertEqual(m.call_count, 1)
            with mock.patch('warnings.warn') as m:
                self.assertEqual(install(exes[0], [exes[1]], None),
                                 (targets[0], [targets[1]], None))
                self.assertEqual(m.call_count, 1)


class TestInstallify(FileTest):
    def _check(self, kind, src, dst, src_kwargs={}, dst_kwargs={}, **kwargs):
        f = kind(src, **src_kwargs, **kwargs)
        installed = kind(dst, **dst_kwargs, **kwargs)
        self.assertSameFile(install.installify(f), installed)
        for name in ('winnt', 'linux'):
            env = MockEnv(target.platform_info(name))
            dst_kwargs_cross = {k: v.cross(env) if v.destdir else v
                                for k, v in dst_kwargs.items()}
            installed = kind(dst.cross(env), **dst_kwargs_cross, **kwargs)
            self.assertSameFile(install.installify(f, cross=env), installed)

    def test_installify(self):
        self._check(Executable, Path('foo/bar', Root.srcdir),
                    Path('bar', InstallRoot.bindir, True), format=None)
        self._check(Executable, Path('foo/bar', Root.builddir),
                    Path('foo/bar', InstallRoot.bindir, True), format=None)

    def test_installify_header(self):
        self._check(HeaderFile, Path('foo/bar.hpp', Root.srcdir),
                    Path('bar.hpp', InstallRoot.includedir, True), lang='c++')
        self._check(HeaderFile, Path('foo/bar.hpp', Root.builddir),
                    Path('foo/bar.hpp', InstallRoot.includedir, True),
                    lang='c++')

        self._check(HeaderDirectory, Path('foo/bar', Root.srcdir),
                    Path('', InstallRoot.includedir, True))
        self._check(HeaderDirectory, Path('foo/bar', Root.builddir),
                    Path('', InstallRoot.includedir, True))

    def test_installify_private(self):
        self._check(DllBinary, Path('foo/bar.dll', Root.srcdir),
                    Path('bar.dll', InstallRoot.bindir, True),
                    {'import_path': Path('foo/bar.lib', Root.srcdir),
                     'export_path': Path('foo/bar.exp', Root.srcdir)},
                    {'import_path': Path('bar.lib', InstallRoot.libdir, True),
                     'export_path': Path('foo/bar.exp', Root.srcdir)},
                    format=None, lang='c++')
        self._check(DllBinary, Path('foo/bar.dll', Root.builddir),
                    Path('foo/bar.dll', InstallRoot.bindir, True),
                    {'import_path': Path('foo/bar.lib', Root.builddir),
                     'export_path': Path('foo/bar.exp', Root.builddir)},
                    {'import_path': Path('foo/bar.lib', InstallRoot.libdir,
                                         True),
                     'export_path': Path('foo/bar.exp', Root.builddir)},
                    format=None, lang='c++')

    def test_installify_not_installable(self):
        f = File(Path('foo/bar.txt', Root.srcdir))
        self.assertRaises(TypeError, install.installify, f)

        hdr = PrecompiledHeader(Path('foo/bar.pch', Root.srcdir), 'c++')
        self.assertRaises(TypeError, install.installify, hdr)

    def test_installify_non_file(self):
        self.assertRaises(TypeError, install.installify, Phony('name'))

    def test_installify_absolute(self):
        exe = Executable(Path('/foo/bar', Root.absolute), None)
        self.assertRaises(ValueError, install.installify, exe)


class TestMakeBackend(BuiltinTest):
    def test_no_install(self):
        makefile = make.Makefile(None)

        with mock.patch.object(make.Makefile, 'rule') as mrule, \
             mock.patch('logging.log'):  # noqa
            install.make_install_rule(self.build, makefile, self.env)
            mrule.assert_not_called()

    def test_install(self):
        makefile = make.Makefile(None)
        src = self.context['source_file']('main.cpp')
        exe = self.context['executable']('exe', src)
        self.context['install'](exe)

        with mock.patch.object(make.Makefile, 'rule') as mrule, \
             mock.patch('logging.log'):  # noqa
            install.make_install_rule(self.build, makefile, self.env)
            self.assertEqual(mrule.mock_calls, [
                mock.call(target='install', deps='all', phony=True,
                          recipe=AlwaysEqual()),
                mock.call(target='uninstall', phony=True, recipe=AlwaysEqual())
            ])


class TestNinjaBackend(BuiltinTest):
    def test_no_install(self):
        ninjafile = ninja.NinjaFile(None)

        with mock.patch.object(ninja.NinjaFile, 'build') as mbuild, \
             mock.patch('logging.log'):  # noqa
            install.ninja_install_rule(self.build, ninjafile, self.env)
            mbuild.assert_not_called()

    def test_install(self):
        ninjafile = ninja.NinjaFile(None)
        src = self.context['source_file']('main.cpp')
        exe = self.context['executable']('exe', src)
        self.context['install'](exe)

        with mock.patch.object(ninja.NinjaFile, 'build') as mbuild, \
             mock.patch.object(ninja.NinjaFile, 'has_build',
                               return_value=True), \
             mock.patch('logging.log'):  # noqa
            install.ninja_install_rule(self.build, ninjafile, self.env)
            self.assertEqual(mbuild.mock_calls, [
                mock.call(output='install', inputs=['all'], implicit=['PHONY'],
                          order_only=None, rule='command',
                          variables=AlwaysEqual()),
                mock.call(output='uninstall', inputs=None, implicit=['PHONY'],
                          order_only=None, rule='command',
                          variables=AlwaysEqual()),
            ])
