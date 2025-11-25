import ntpath
import os.path
import posixpath
import unittest.mock
from itertools import zip_longest

from .. import *
from ..parameterize import ParameterizedTestCase

from bfg9000 import iterutils
from bfg9000.file_types import Node
from bfg9000.path import Path
from bfg9000.platforms.posix import PosixPath
from bfg9000.platforms.windows import WindowsPath


# Fix the mock lib's mock_open function to work with iter(); note: this is
# already fixed in Python 3.7.1.
def mock_open(*args, **kwargs):
    mo = unittest.mock.mock_open(*args, **kwargs)
    handle = mo.return_value
    handle.__iter__.side_effect = lambda: iter(handle.readlines.side_effect())
    return mo


def skip_if_platform(platform):
    return skip_pred(lambda x: x.platform_name == platform,
                     'not supported for platform "{}"'.format(platform))


def only_if_platform(platform):
    return skip_pred(lambda x: x.platform_name != platform,
                     'only supported for platform "{}"'.format(platform))


class AttrDict:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CrossPlatformTestCase(ParameterizedTestCase,
                            params=['linux', 'winnt', 'macos'],
                            dest='platform_name'):
    def __init__(self, *args, clear_variables=False, variables={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = make_env(platform=self.platform_name,
                            clear_variables=clear_variables,
                            variables=variables)

    @property
    def Path(self):
        return self.env.host_platform.Path


class PathTestCase(ParameterizedTestCase,
                   params={
                       'native': (Path, os.path),
                       'posix': (PosixPath, posixpath),
                       'windows': (WindowsPath, ntpath),
                   }, dest=('Path', 'ospath')):
    pass


class FileTestCase(TestCase):
    excluded_file_fields = {'creator', 'forward_opts', 'post_install'}

    def assertSameFile(self, a, b):
        def diff_node(a, b, attr_path=()):
            diffs = []
            if type(a) is not type(b):
                diffs.append((attr_path, type(a), type(b)))
            elif iterutils.ismapping(a) and iterutils.ismapping(b):
                for i in sorted(set(a.keys()) | set(b.keys())):
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(a.get(i), b.get(i), curr_path))
            elif iterutils.isiterable(a) and iterutils.isiterable(b):
                for i, (ai, bi) in enumerate(zip_longest(a, b)):
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(ai, bi, curr_path))
            elif isinstance(a, Node) and isinstance(b, Node):
                seen_key = (id(a), id(b))
                if seen_key in seen:
                    return []
                seen.add(seen_key)

                for i in sorted(set(vars(a)) | set(vars(b))):
                    if i in self.excluded_file_fields:
                        continue
                    curr_path = attr_path + (i,)
                    diffs.extend(diff_node(
                        getattr(a, i, None), getattr(b, i, None), curr_path
                    ))
            elif a != b:
                diffs.append((attr_path, a, b))

            return diffs

        seen = set()
        diffs = diff_node(a, b)
        if diffs:
            raise AssertionError('mismatched files:\n' + '\n'.join(
                '  {}: {!r} != {!r}'.format(
                    '.'.join(str(j) for j in i[0]), *i[1:]
                ) for i in diffs
            ))
