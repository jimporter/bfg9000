from ... import *  # noqa

from bfg9000.path import Path, Root


class FakeEnv:
    def getvar(self, name, default=''):
        return default

    @property
    def srcdir(self):
        return Path('/path', Root.absolute)
