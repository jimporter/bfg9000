import json
import os.path
from io import StringIO

from ... import *

from bfg9000 import file_types
from bfg9000.backends.compdb.writer import *
from bfg9000.path import Path, Root
from bfg9000.safe_str import shell_literal
from bfg9000.shell import shell_list, quote as shell_quote


class TestCompDB(TestCase):
    def setUp(self):
        self.env = make_env()
        self.compdb = CompDB(self.env)
        self.base_dirs = self.env.base_dirs.copy()
        self.base_dirs[path.Root.builddir] = None

    def _db_to_json(self):
        out = StringIO()
        self.compdb.write(out)
        return json.loads(out.getvalue())

    def test_command(self):
        file = file_types.File(Path('foo.c', Root.srcdir))
        output = file_types.File(Path('foo.o'))
        self.compdb.append(file=file, output=output, command='cc foo.c')

        self.assertEqual(self._db_to_json(), [
            {'directory': self.env.builddir.string(),
             'command': 'cc foo.c',
             'file': file.path.string(self.base_dirs),
             'output': output.path.string(self.base_dirs)},
        ])

    def test_arguments(self):
        file = file_types.File(Path('foo.c', Root.srcdir))
        output = file_types.File(Path('foo.o'))
        self.compdb.append(file=file, output=output,
                           arguments=['cc', file, '-o' + output])

        self.assertEqual(self._db_to_json(), [
            {'directory': self.env.builddir.string(),
             'arguments': ['cc', file.path.string(self.base_dirs),
                           '-o' + output.path.string(self.base_dirs)],
             'file': file.path.string(self.base_dirs),
             'output': 'foo.o'},
        ])

    def test_arguments_shell_list(self):
        file = file_types.File(Path('foo.c', Root.srcdir))
        output = file_types.File(Path('foo.o'))
        self.compdb.append(file=file, output=output, arguments=shell_list([
            'cmd', shell_literal('<'), file, shell_literal('>>'), output
        ]))

        self.assertEqual(self._db_to_json(), [
            {'directory': self.env.builddir.string(),
             'command': 'cmd < {} >> {}'.format(
                 file.path.string(self.base_dirs),
                 output.path.string(self.base_dirs)
             ),
             'file': file.path.string(self.base_dirs),
             'output': 'foo.o'},
        ])

    def test_arguments_funky_shell_list(self):
        file = file_types.File(Path('foo.c', Root.srcdir))
        output = file_types.File(Path('foo.o'))
        self.compdb.append(file=file, output=output, arguments=shell_list([
            'cmd', shell_literal('<') + 'foo bar'
        ]))

        self.assertEqual(self._db_to_json(), [
            {'directory': self.env.builddir.string(),
             'command': 'cmd <{}'.format(shell_quote('foo bar')),
             'file': file.path.string(self.base_dirs),
             'output': 'foo.o'},
        ])

    def test_directory(self):
        directory = self.env.builddir.append('subdir')
        file = file_types.File(Path('foo.c', Root.srcdir))
        output = file_types.File(Path('foo.o'))
        self.compdb.append(directory=directory, file=file, output=output,
                           command='cc foo.c')

        self.assertEqual(self._db_to_json(), [
            {'directory': directory.string(),
             'command': 'cc foo.c',
             'file': file.path.string(self.base_dirs),
             'output': os.path.join('..', 'foo.o')},
        ])

    def test_no_output(self):
        file = file_types.File(Path('foo.c', Root.srcdir))
        self.compdb.append(file=file, command='cc foo.c')

        self.assertEqual(self._db_to_json(), [
            {'directory': self.env.builddir.string(),
             'command': 'cc foo.c',
             'file': file.path.string(self.base_dirs)},
        ])

    def test_no_command_or_arguments(self):
        with self.assertRaises(ValueError):
            self.compdb.append(
                file=file_types.File(Path('foo.c', Root.srcdir))
            )
