import fnmatch
import re

try:
    from enum import Flag
except ImportError:
    from enum import IntEnum as Flag

from .iterutils import find_index
from .objutils import memoize, objectify
from .path import Path, Root


class Glob:
    class Type(Flag):
        file = 1
        dir = 2
        any = file | dir

        @classmethod
        def from_char(cls, s):
            if s == 'f':
                return cls.file
            elif s == 'd':
                return cls.dir
            elif s == '*':
                return cls.any
            raise ValueError('unknown type {!r}'.format(s))

    def __init__(self, type, isdir):
        if type is None:
            type = self.Type.dir if isdir else self.Type.file
        else:
            type = objectify(type, self.Type, self.Type.from_char)
            if type == self.Type.file and isdir:
                raise ValueError("type is 'f' but pattern is a directory")
        self.type = type


class PathGlob(Glob):
    _glob_ex = re.compile(r'[*?[]')
    _starstar = object()

    class Result:
        def __init__(self, matched, recursive=False):
            self.matched = matched
            self.recursive = False if matched else recursive

        def __bool__(self):
            return self.matched

        def __eq__(self, rhs):
            return (self.matched == rhs.matched and
                    self.recursive == rhs.recursive)

        def __and__(self, rhs):
            return type(self)(self.matched and rhs.matched,
                              self.recursive or rhs.recursive)

        def __or__(self, rhs):
            return type(self)(self.matched or rhs.matched,
                              self.recursive and rhs.recursive)

        def __repr__(self):
            return '<{}({}, {})>'.format(type(self).__name__, self.matched,
                                         self.recursive)

    def __init__(self, pattern, type=None, root=Root.srcdir):
        path = Path.ensure(pattern, root)
        super().__init__(type, path.directory)
        bits = path.split()

        first_glob = find_index(self._is_glob, bits)
        if first_glob is None:
            raise ValueError('{!r} is not a glob'.format(pattern))

        self.base = Path(Path.sep.join(bits[0:first_glob]), path.root,
                         directory=True)
        self.bits = list(self._translate_bits(bits[first_glob:]))

    @classmethod
    def _is_glob(cls, s):
        return bool(cls._glob_ex.search(s))

    @classmethod
    def _translate_bits(cls, bits):
        starstar = False
        for i in bits:
            if i == '**':
                # This line is fully-covered, but coverage.py can't detect it
                # correctly...
                if not starstar:  # pragma: no branch
                    starstar = True
                    yield cls._starstar
                continue

            starstar = False
            if cls._is_glob(i):
                yield re.compile(fnmatch.translate(i)).match
            else:
                assert i
                yield cls._match_string(i)

    @staticmethod
    def _match_string(s):
        return lambda x: x == s

    @memoize
    def _base_depth(self):
        return len(self.base.split())

    def match(self, path, skip_base=False):
        if skip_base:
            def iter_from(seq, n):
                for i in range(n, len(seq)):
                    yield seq[i]
            path_iter = iter_from(path.split(), self._base_depth())
        else:
            if path.root != self.base.root:
                return self.Result(False, recursive=False)

            path_iter = iter(path.split())
            for i in self.base.split():
                p = next(path_iter, None)
                if p is None or p != i:
                    # `path` is either a parent of or diverges from our
                    # pattern. This should only occur when we have multiple
                    # `PathGlob`s for a given filter.
                    return self.Result(False, recursive=False)

        recursing = False
        for i in self.bits:
            if i is self._starstar:
                recursing = True
                continue

            if recursing:
                p = None
                for p in path_iter:
                    if i(p):
                        break
                else:
                    return self.Result(False, recursive=False)
                recursing = False
                continue

            p = next(path_iter, None)
            if p is None:
                # `path` is a parent of our pattern.
                return self.Result(False, recursive=False)
            if not i(p):
                # `path` diverges from our pattern, so no children of `path`
                # could ever match.
                return self.Result(False, recursive=True)

        if next(path_iter, None) is not None:
            if not recursing:
                # `path` is a child of our pattern, and we're not looking for
                # children.
                return self.Result(False, recursive=True)

        # `path` matches our pattern. Check if it's the right file type.
        found_type = self.Type.dir if path.directory else self.Type.file
        if self.type & found_type:
            return self.Result(True)
        return self.Result(False, recursive=False)


class NameGlob(Glob):
    _slash_ex = re.compile(r'[\\/]+$')

    def __init__(self, pattern, type=None):
        pattern, n = re.subn(self._slash_ex, '', pattern)
        super().__init__(type, n > 0)
        self.pattern = re.compile(fnmatch.translate(pattern))

    def match(self, path):
        if self.pattern.match(path.basename()):
            found_type = self.Type.dir if path.directory else self.Type.file
            return bool(self.type & found_type)
        return False
