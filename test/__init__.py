import functools
import itertools
import mock
import unittest
from six import assertRegex, assertRaisesRegex

from bfg9000.environment import Environment
from bfg9000.path import abspath, Path, Root

__all__ = ['assertNotRegex', 'assertRaisesRegex', 'assertRegex', 'load_tests',
           'make_env', 'parameterize_tests', 'skip_if', 'skip_pred',
           'TestCase', 'xfail_if']


def make_env(platform=None, clear_variables=False):
    args = (Path('bfgdir', Root.srcdir), None, None, abspath('srcdir'),
            abspath('builddir'), {}, (False, False))
    if platform:
        with mock.patch('bfg9000.platforms.core.platform_name',
                        return_value=platform):
            env = Environment(*args)
    else:
        env = Environment(*args)

    if clear_variables:
        env.variables = {}
    return env


def _add_hide_func(thing, predicate):
    if not hasattr(thing, '_test_hide_if'):
        thing._test_hide_if = predicate
    else:
        old = thing._test_hide_if
        thing._test_hide_if = lambda self: old(self) or predicate(self)


def skip_if(skip, msg='skipped', hide=False):
    if hide:
        def wrap(fn):
            if skip:
                _add_hide_func(fn, lambda self: True)
            return fn

        return wrap
    return unittest.skipIf(skip, msg)


def skip_pred(predicate, msg='skipped', hide=False):
    def wrap(fn):
        if hide:
            _add_hide_func(fn, predicate)
            return fn

        if isinstance(fn, type):
            @functools.wraps(fn, assigned=['__name__', '__module__'],
                             updated=[])
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


# For some reason, six doesn't have this wrapper...
def assertNotRegex(self, *args, **kwargs):
    if hasattr(self, 'assertNotRegex'):
        return self.assertNotRegex(*args, **kwargs)
    else:
        return self.assertNotRegexpMatches(*args, **kwargs)


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        unittest.TestCase.__init__(self, *args, **kwargs)

    def _hideTest(self):
        test_method = getattr(self, self._testMethodName)
        return ( (hasattr(self, '_test_hide_if') and
                  self._test_hide_if()) or
                 (hasattr(test_method, '_test_hide_if') and
                  test_method._test_hide_if(self)) )

    def parameterize(self):
        return [] if self._hideTest() else [self]


def parameterize_tests(tests, **kwargs):
    result = []
    for i in itertools.product(*kwargs.values()):
        try:
            params = dict(zip(kwargs.keys(), i))
            params.update(tests._kwargs)
            copy = tests.__class__(*tests._args, **params)
            if not copy._hideTest():
                result.append(copy)
        except unittest.SkipTest:
            pass
    return result


def load_tests(loader, standard_tests, pattern):
    all_tests = unittest.TestSuite()
    for suite in standard_tests:
        for case in suite:
            all_tests.addTests(case.parameterize()
                               if hasattr(case, 'parameterize') else case)
    return all_tests
