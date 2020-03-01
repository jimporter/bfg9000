from . import *


class TestBadBuild(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('bad_build', configure=False, *args, **kwargs)

    def test_bad_build(self):
        self.configure(returncode=1)
