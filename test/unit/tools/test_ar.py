from unittest import mock

from .. import *

from bfg9000 import file_types, options as opts
from bfg9000.tools.ar import ArLinker
from bfg9000.versioning import Version


def mock_which(*args, **kwargs):
    return ['command']


class TestArLinker(CrossPlatformTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(clear_variables=True, *args, **kwargs)

    def setUp(self):
        with mock.patch('bfg9000.shell.which', mock_which):
            fmt = self.env.target_platform.object_format
            self.ar = ArLinker(AttrDict(object_format=fmt), self.env, 'ar',
                               ['ar'], 'arflags', [])

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

    def test_call(self):
        self.assertEqual(self.ar(['in'], 'out'),
                         [self.ar, 'out', 'in'])
        self.assertEqual(self.ar(['in'], 'out', ['flags']),
                         [self.ar, 'flags', 'out', 'in'])

    def test_output_file(self):
        fmt = self.env.target_platform.object_format
        self.assertEqual(
            self.ar.output_file('foo', AttrDict(langs=['c++'])),
            file_types.StaticLibrary(Path('libfoo.a'), fmt, ['c++'])
        )

    def test_flags_empty(self):
        self.assertEqual(self.ar.flags(opts.option_list()), [])

    def test_flags_string(self):
        self.assertEqual(self.ar.flags(opts.option_list('-v')), ['-v'])

    def test_flags_invalid(self):
        with self.assertRaises(TypeError):
            self.ar.flags(opts.option_list(123))
