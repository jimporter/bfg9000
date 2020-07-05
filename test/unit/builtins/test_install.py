from unittest import mock

from .common import AlwaysEqual, BuiltinTest

from bfg9000.backends.make import syntax as make
from bfg9000.backends.ninja import syntax as ninja
from bfg9000.builtins import compile, default, install, link, packages, project  # noqa
from bfg9000.file_types import Executable, Phony
from bfg9000.path import Path, Root, InstallRoot


class TestInstall(BuiltinTest):
    def test_install_none(self):
        self.assertEqual(self.context['install'](), None)
        self.assertEqual(self.build['install'].explicit, [])
        self.assertEqual(self.build['install'].implicit, [])

    def test_install_single(self):
        exe = Executable(Path('exe', Root.srcdir), None)
        installed = Executable(Path('exe', InstallRoot.bindir), None)
        self.assertEqual(self.context['install'](exe), installed)
        self.assertEqual(self.build['install'].explicit, [exe])
        self.assertEqual(self.build['install'].implicit, [exe])

    def test_install_multiple(self):
        exe1 = Executable(Path('exe1', Root.srcdir), None)
        exe2 = Executable(Path('exe2', Root.srcdir), None)
        installed1 = Executable(Path('exe1', InstallRoot.bindir), None)
        installed2 = Executable(Path('exe2', InstallRoot.bindir), None)
        self.assertEqual(self.context['install'](exe1, exe2),
                         (installed1, installed2))
        self.assertEqual(self.build['install'].explicit, [exe1, exe2])
        self.assertEqual(self.build['install'].implicit, [exe1, exe2])

    def test_install_nested_multiple(self):
        exe1 = Executable(Path('exe1', Root.srcdir), None)
        exe2 = Executable(Path('exe2', Root.srcdir), None)
        installed1 = Executable(Path('exe1', InstallRoot.bindir), None)
        installed2 = Executable(Path('exe2', InstallRoot.bindir), None)
        self.assertEqual(self.context['install'](exe1, [exe2], None),
                         (installed1, [installed2], None))
        self.assertEqual(self.build['install'].explicit, [exe1, exe2])
        self.assertEqual(self.build['install'].implicit, [exe1, exe2])

    def test_install_add_to_default(self):
        exe = Executable(Path('exe', Root.srcdir), None)
        exe.creator = 'creator'
        installed = Executable(Path('exe', InstallRoot.bindir), None)
        self.assertEqual(self.context['install'](exe), installed)
        self.assertEqual(self.build['install'].explicit, [exe])
        self.assertEqual(self.build['install'].implicit, [exe])
        self.assertEqual(self.build['defaults'].outputs, [exe])

    def test_invalid(self):
        phony = Phony('name')
        self.assertRaises(TypeError, self.context['install'], phony)

        exe = Executable(Path('/path/to/exe', Root.absolute), None)
        self.assertRaises(ValueError, self.context['install'], exe)

    def test_cant_install(self):
        with mock.patch('bfg9000.builtins.install.can_install',
                        return_value=False), \
             mock.patch('warnings.warn') as m:  # noqa
            exe = Executable(Path('exe', Root.srcdir), None)
            installed = Executable(Path('exe', InstallRoot.bindir), None)
            self.assertEqual(self.context['install'](exe), installed)
            self.assertEqual(m.call_count, 1)


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
