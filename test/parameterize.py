from collections.abc import Iterable, Mapping

from . import TestCase

from bfg9000.iterutils import default_sentinel

# HACK: This is a hacky way of parameterizing TestCases without needing to mess
# with the test loader. This works by overriding `__dir__` so that it produces
# a list of test methods with parameterized names, like `test_foo.param`. These
# parameterized names are special `TestMethodStr` objects which carry along the
# real method name and the test param.


class TestMethodStr(str):
    def __new__(cls, *args, method_name, param, **kwargs):
        s = str.__new__(cls, *args, **kwargs)
        s.test_method_name = method_name
        s.test_param = param
        return s


class PTCMeta(type):
    test_prefix = 'test'

    def __new__(cls, clsname, bases, attrs, params=default_sentinel,
                dest=default_sentinel):
        t = super().__new__(cls, clsname, bases, attrs)

        if params is not default_sentinel:
            t._test_params = params
        elif not hasattr(t, '_test_params'):
            t._test_params = []

        if dest is not default_sentinel:
            t._test_dest = dest
        elif not hasattr(t, '_test_dest'):
            t._test_dest = 'test_param'

        return t

    def __dir__(cls):
        def make_dir(entries):
            for entry in entries:
                if entry.startswith(PTCMeta.test_prefix):
                    if isinstance(cls._test_params, Mapping):
                        for k, v in cls._test_params.items():
                            yield TestMethodStr('{}.{}'.format(entry, k),
                                                method_name=entry, param=v)
                    elif isinstance(cls._test_params, Iterable):
                        for i in cls._test_params:
                            yield TestMethodStr('{}.{}'.format(entry, i),
                                                method_name=entry, param=i)
                    else:
                        raise TypeError('non-iterable test params')
                else:
                    yield entry

        return list(make_dir(type.__dir__(cls)))

    def __getattr__(cls, attr):
        attr, *params = attr.split('.')
        return type.__getattribute__(cls, attr)


class ParameterizedTestCase(TestCase, metaclass=PTCMeta):
    def __init__(self, methodName='runTest'):
        if isinstance(methodName, TestMethodStr):
            super().__init__(methodName.test_method_name)
            if isinstance(self._test_dest, str):
                setattr(self, self._test_dest, methodName.test_param)
            else:
                for attr, value in zip(self._test_dest, methodName.test_param):
                    setattr(self, attr, value)
            self._testMethodName = str(methodName)
        else:
            super().__init__(methodName)

    def __getattr__(self, attr):
        attr, *params = attr.split('.')
        return super().__getattribute__(attr)
