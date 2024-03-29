from unittest import mock

from . import *

from bfg9000.exceptions import PackageResolutionError
from bfg9000.packages import Framework
from bfg9000.path import InstallRoot
from bfg9000.tools.mopack import Mopack, get_linkage, to_frameworks


class TestMopack(ToolTestCase):
    tool_type = Mopack

    def test_env(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']):
            self.assertIsInstance(self.env.tool('mopack'), Mopack)

    def test_call_resolve(self):
        prefix = self.env.install_dirs[InstallRoot.prefix]
        self.assertEqual(self.tool('resolve', 'mopack.yml'),
                         [self.tool, 'resolve', '-dprefix=' + prefix, '--',
                          'mopack.yml'])
        self.assertEqual(self.tool('resolve', 'mopack.yml', flags=['--foo']),
                         [self.tool, 'resolve', '-dprefix=' + prefix, '--foo',
                          '--', 'mopack.yml'])
        self.assertEqual(self.tool('resolve', 'mopack.yml', directory='dir'),
                         [self.tool, 'resolve', '--directory', 'dir',
                          '-dprefix=' + prefix, '--', 'mopack.yml'])

    def test_call_linkage(self):
        self.assertEqual(self.tool('linkage', 'pkg'),
                         [self.tool, 'linkage', '--json', 'pkg'])
        self.assertEqual(self.tool('linkage', 'pkg', submodules='sub'),
                         [self.tool, 'linkage', '--json', 'pkg[sub]'])
        self.assertEqual(self.tool('linkage', 'pkg', directory='dir'),
                         [self.tool, 'linkage', '--directory', 'dir', '--json',
                          'pkg'])

    def test_call_deploy(self):
        self.assertEqual(self.tool('deploy'), [self.tool, 'deploy'])
        self.assertEqual(self.tool('deploy', directory='dir'),
                         [self.tool, 'deploy', '--directory', 'dir'])

    def test_call_clean(self):
        self.assertEqual(self.tool('clean'), [self.tool, 'clean'])
        self.assertEqual(self.tool('clean', directory='dir'),
                         [self.tool, 'clean', '--directory', 'dir'])

    def test_call_list_files(self):
        self.assertEqual(self.tool('list_files'),
                         [self.tool, 'list-files', '--json'])
        self.assertEqual(self.tool('list_files', directory='dir'),
                         [self.tool, 'list-files', '--directory', 'dir',
                          '--json'])

    def test_call_invalid(self):
        self.assertRaises(TypeError, self.tool, 'unknown')


class TestGetLinkage(ToolTestCase):
    tool_type = Mopack

    def test_success(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute',
                        return_value='{"type": "unknown"}'):
            self.assertEqual(get_linkage(self.env, 'foo'), {'type': 'unknown'})

    def test_failure(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', side_effect=OSError()), \
             self.assertRaises(PackageResolutionError):
            get_linkage(self.env, 'foo')


class TestToFrameworks(TestCase):
    def test_lib(self):
        self.assertEqual(to_frameworks(['lib']), ['lib'])

    def test_framework(self):
        self.assertEqual(to_frameworks([{'type': 'framework', 'name': 'fw'}]),
                         [Framework('fw')])

    def test_mixed(self):
        self.assertEqual(to_frameworks(
            ['lib', {'type': 'framework', 'name': 'fw'}]
        ), ['lib', Framework('fw')])

    def test_unknown(self):
        with self.assertRaises(ValueError):
            to_frameworks([{'type': 'unknown'}])
