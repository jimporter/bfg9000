import mock
import unittest

from ... import make_env

from bfg9000 import options as opts
from bfg9000.tools.ar import ArLinker
from bfg9000.versioning import Version


def mock_which(*args, **kwargs):
    return ['command']


class TestArLinker(unittest.TestCase):
    def setUp(self):
        self.env = make_env()
        with mock.patch('bfg9000.shell.which', mock_which):
            self.ar = ArLinker(None, self.env)

    def test_flavor(self):
        self.assertEqual(self.ar.flavor, 'ar')

    def test_gnu_ar(self):
        def mock_execute(*args, **kwargs):
            return 'GNU ar (binutils) 2.26.1'

        with mock.patch('bfg9000.shell.execute', mock_execute):
            self.assertEqual(self.ar.brand, 'gnu')
            self.assertEqual(self.ar.version, Version('2.26.1'))

    def test_unknown_brand(self):
        def mock_execute(*args, **kwargs):
            return 'unknown'

        with mock.patch('bfg9000.shell.execute', mock_execute):
            self.assertEqual(self.ar.brand, 'unknown')
            self.assertEqual(self.ar.version, None)

    def test_broken_brand(self):
        def mock_execute(*args, **kwargs):
            raise OSError()

        with mock.patch('bfg9000.shell.execute', mock_execute):  # noqa
            self.assertEqual(self.ar.brand, 'unknown')
            self.assertEqual(self.ar.version, None)

    def test_flags_empty(self):
        self.assertEqual(self.ar.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.ar.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.ar.flags(opts.option_list(123))
