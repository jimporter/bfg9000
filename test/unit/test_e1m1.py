import mock

from . import *

from bfg9000 import e1m1


# Just ensure these don't throw any unexpected errors...
class TestE1M1(TestCase):
    def test_play(self):
        with mock.patch('bfg9000.e1m1._do_play'):
            e1m1.play(120, False)

    def test_play_long(self):
        with mock.patch('bfg9000.e1m1._do_play'):
            e1m1.play(120, True)
