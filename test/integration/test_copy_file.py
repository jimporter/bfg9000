import os
import sys
from os.path import join as pjoin

from . import *
from bfg9000.versioning import SpecifierSet


class TestCopyFile(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('copy_file', configure=False, *args, **kwargs)

    def split_path(self, target):
        path, name = os.path.split(self.target_path(target))
        return path, pjoin('.', name)

    def test_copy(self):
        self.configure(extra_args=['--mode=copy'])
        self.build(executable('simple'))

        # Change to the directory containing the executable so that we can read
        # the data file correctly under MSBuild.
        path, exe = self.split_path(executable('simple'))
        os.chdir(path)

        self.assertOutput([exe], 'Hello from a file!\n')
        self.assertTrue(os.path.isfile(pjoin('dir', 'data.txt')))
        if hasattr(os.path, 'samefile'):
            self.assertFalse(os.path.samefile(
                pjoin('dir', 'data.txt'), pjoin(self.srcdir, 'dir', 'data.txt')
            ))

    def test_symlink(self):
        self.configure(extra_args=['--mode=symlink'])
        self.build(executable('simple'))

        path, exe = self.split_path(executable('simple'))
        os.chdir(path)

        self.assertOutput([exe], 'Hello from a file!\n')
        supports_symlink = (env.backend != 'msbuild' or (
            env.backend_version and env.backend_version in SpecifierSet('>=15')
        ))
        if ( env.host_platform.family == 'windows' and sys.version[0] == 2 and
             supports_symlink ):
            self.assertTrue(os.path.islink(pjoin('dir', 'data.txt')))

    def test_hardlink(self):
        self.configure(extra_args=['--mode=hardlink'])
        self.build(executable('simple'))

        path, exe = self.split_path(executable('simple'))
        os.chdir(path)

        self.assertOutput([exe], 'Hello from a file!\n')
        self.assertTrue(os.path.isfile(pjoin('dir', 'data.txt')))
        if hasattr(os.path, 'samefile'):
            self.assertTrue(os.path.samefile(
                pjoin('dir', 'data.txt'), pjoin(self.srcdir, 'dir', 'data.txt')
            ))
