import mock
import unittest

from bfg9000.environment import Environment
from bfg9000.tools.ar import ArLinker
from bfg9000.versioning import Version

env = Environment(None, None, None, None, None, {}, (False, False), None)


def mock_which(*args, **kwargs):
    return ['command']


class TestArLinker(unittest.TestCase):
    def test_flavor(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            ar = ArLinker(None, env)
        self.assertEqual(ar.flavor, 'ar')

    def test_gnu_ar(self):
        def mock_execute(*args, **kwargs):
            return 'GNU ar (binutils) 2.26.1'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            ar = ArLinker(None, env)
            self.assertEqual(ar.brand, 'gnu')
            self.assertEqual(ar.version, Version('2.26.1'))

    def test_unknown_brand(self):
        def mock_execute(*args, **kwargs):
            return 'unknown'

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            ar = ArLinker(None, env)
            self.assertEqual(ar.brand, 'unknown')
            self.assertEqual(ar.version, None)

    def test_broken_brand(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('bfg9000.shell.which', mock_which), \
             mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            ar = ArLinker(None, env)
            self.assertEqual(ar.brand, 'unknown')
            self.assertEqual(ar.version, None)
