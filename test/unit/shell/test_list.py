from .. import *

from bfg9000.shell.list import shell_list


class TestShellList(TestCase):
    def test_repr(self):
        x = shell_list([1, 2, 3])
        self.assertEqual(repr(x), '<shell_list([1, 2, 3])>')

    def test_concat(self):
        x = shell_list([1, 2, 3])
        y = [4, 5]

        self.assertEqual(x + y, shell_list([1, 2, 3, 4, 5]))
        self.assertEqual(type(x + y), shell_list)

        self.assertEqual(y + x, shell_list([4, 5, 1, 2, 3]))
        self.assertEqual(type(y + x), shell_list)

    def test_append(self):
        x = shell_list([1, 2, 3])
        x += [4, 5]
        self.assertEqual(x, shell_list([1, 2, 3, 4, 5]))
        self.assertEqual(type(x), shell_list)

        x = [4, 5]
        x += shell_list([1, 2, 3])
        self.assertEqual(x, shell_list([4, 5, 1, 2, 3]))
        self.assertEqual(type(x), shell_list)

    def test_slice(self):
        x = shell_list([1, 2, 3])

        self.assertEqual(x[:], shell_list([1, 2, 3]))
        self.assertEqual(type(x[:]), shell_list)

        self.assertEqual(x[0:2], shell_list([1, 2]))
        self.assertEqual(type(x[0:2]), shell_list)

        self.assertEqual(x[0:3:2], shell_list([1, 3]))
        self.assertEqual(type(x[0:3:2]), shell_list)
