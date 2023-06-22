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
        self.assertEqual(y + x, shell_list([4, 5, 1, 2, 3]))

    def test_append(self):
        x = shell_list([1, 2, 3])
        x += [4, 5]
        self.assertEqual(x, shell_list([1, 2, 3, 4, 5]))

        x = [4, 5]
        x += shell_list([1, 2, 3])
        self.assertEqual(x, shell_list([4, 5, 1, 2, 3]))

    def test_slice(self):
        x = shell_list([1, 2, 3])

        self.assertEqual(x[:], shell_list([1, 2, 3]))
        self.assertEqual(x[0:2], shell_list([1, 2]))
        self.assertEqual(x[0:3:2], shell_list([1, 3]))

    def test_equality(self):
        x = shell_list([1, 2, 3])

        self.assertTrue(x == shell_list([1, 2, 3]))
        self.assertTrue(x != shell_list([1, 2, 3, 4]))
        self.assertTrue(x != [1, 2, 3])
        self.assertTrue(x != [1, 2, 3, 4])
        self.assertTrue([1, 2, 3] != x)
        self.assertTrue([1, 2, 3, 4] != x)
