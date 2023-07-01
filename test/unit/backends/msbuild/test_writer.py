from unittest import mock

from ... import *

from bfg9000.backends.msbuild.writer import version
from bfg9000.versioning import Version


def mock_bad_execute(*args, **kwargs):
    raise OSError()


class TestMsBuildVersion(TestCase):
    def test_good(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', return_value='MSBuild 1.23'):
            self.assertEqual(version({}), Version('1.23'))

    def test_unrecognized_version(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', return_value='MSBuild'):
            self.assertEqual(version({}), None)

    def test_not_found(self):
        with mock.patch('bfg9000.shell.which',
                        side_effect=FileNotFoundError()):
            self.assertEqual(version({}), None)

    def test_bad_execute(self):
        with mock.patch('bfg9000.shell.which', return_value=['command']), \
             mock.patch('bfg9000.shell.execute', mock_bad_execute):
            self.assertEqual(version({}), None)
