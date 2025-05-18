import functools
import unittest

from bfg9000.environment import Environment, EnvVarDict
from bfg9000.path import abspath, InstallRoot

__all__ = ['make_env', 'skip_if', 'skip_pred', 'TestCase', 'xfail_if']


def make_env(platform=None, clear_variables=False, variables={}):
    args = (abspath('bfgdir'), None, None, abspath('srcdir'),
            abspath('builddir'))
    if platform:
        with unittest.mock.patch('bfg9000.platforms.core.platform_name',
                                 return_value=platform):
            env = Environment(*args)
    else:
        env = Environment(*args)
    env.finalize({InstallRoot.prefix: abspath('prefix')}, (False, False),
                 False)

    if clear_variables:
        env.variables = EnvVarDict()
    env.variables.update(variables)
    return env


def skip_if(skip, msg='skipped'):
    return unittest.skipIf(skip, msg)


def skip_pred(predicate, msg='skipped'):
    def wrap(fn):
        if isinstance(fn, type):
            @functools.wraps(fn, assigned=[
                '__name__', '__qualname__', '__module__'
            ], updated=[])
            class Wrap(fn):
                def setUp(self):
                    if predicate(self):
                        raise unittest.SkipTest(msg)
                    fn.setUp(self)

            return Wrap
        else:
            def inner(self, *args, **kwargs):
                if predicate(self):
                    raise unittest.SkipTest(msg)
                return fn(self, *args, **kwargs)
            return inner
    return wrap


def xfail_if(xfail):
    def wrap(fn):
        if xfail:
            return unittest.expectedFailure(fn)
        else:
            return fn
    return wrap


class _StrictPath:
    def __init__(self, path):
        self.path = path

    def __eq__(self, rhs):
        return (self.path == rhs.path and
                self.path.directory == rhs.path.directory)

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return repr(self.path)


class TestCase(unittest.TestCase):
    def assertPathEqual(self, a, b, msg=None):
        self.assertEqual(_StrictPath(a), _StrictPath(b), msg)

    def assertPathListEqual(self, a, b, msg=None):
        self.assertListEqual([_StrictPath(i) for i in a],
                             [_StrictPath(i) for i in b], msg)

    def assertPathDictEqual(self, a, b, msg=None):
        self.assertDictEqual({k: _StrictPath(v) for k, v in a.items()},
                             {k: _StrictPath(v) for k, v in b.items()}, msg)

    def assertPathSetEqual(self, a, b, msg=None):
        self.assertSetEqual({_StrictPath(i) for i in a},
                            {_StrictPath(i) for i in b}, msg)
