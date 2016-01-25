import os
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000.backends.ninja.syntax import *
from bfg9000.platforms import platform_name


class TestNinjaSyntax(unittest.TestCase):
    def test_path_quoting(self):
        out = Writer(StringIO())
        p = path.Path('foo', path.Root.srcdir)
        out.write(p, Syntax.shell)

        quote = '"' if platform_name() == 'windows' else "'"
        self.assertEqual(out.stream.getvalue(),
                         quote + os.path.join('$srcdir', 'foo') + quote)
