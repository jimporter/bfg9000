import os
import unittest
from six.moves import cStringIO as StringIO

from bfg9000 import path
from bfg9000.backends.make.syntax import *


class TestMakeSyntax(unittest.TestCase):
    def test_path_quoting(self):
        out = Writer(StringIO())
        p = path.Path('foo', path.Root.srcdir)
        out.write(p, Syntax.shell)

        self.assertEqual(out.stream.getvalue(),
                         "'" + os.path.join('$(srcdir)', 'foo') + "'")
