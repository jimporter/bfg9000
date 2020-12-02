import fnmatch
import re
from collections import namedtuple
from enum import Enum, Flag
from itertools import zip_longest

from .exceptions import NonGlobError
from .iterutils import find_index, list_view
from .objutils import objectify
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
    _glob_run = namedtuple('_glob_bit', ['matchers', 'length'])

    class Result(Enum):
        yes = 0
        no = 1
        never = 2

        def __bool__(self):
            return self == self.yes

        def __and__(self, rhs):
            return type(self)(max(self.value, rhs.value))

        def __or__(self, rhs):
            return type(self)(min(self.value, rhs.value))

    def __init__(self, pattern, type=None, root=Root.srcdir):
        path = Path.ensure(pattern, root)
        super().__init__(type, path.directory)
        bits = list_view(path.split())

        first_glob = find_index(self._is_glob, bits)
        if first_glob is None:
            raise NonGlobError('{!r} is not a glob'.format(pattern))
        base, glob = bits.split_at(first_glob)

        self.base = Path(Path.sep.join(base), path.root, directory=True)
        self.glob = self._compile_glob(glob)

    @classmethod
    def _is_glob(cls, s):
        return bool(cls._glob_ex.search(s))

    @classmethod
    def _compile_glob(cls, bits):
        # Divide our glob into a series of "runs". Each run is a list of
        # "simple" globs to be matched against path components. In between each
        # run is an implicit `**` pattern.
        globs = [[]]
        starstar = False
        for i in bits:
            if i == '**':
                # This line is fully-covered, but coverage.py can't detect it
                # correctly...
                if not starstar:  # pragma: no branch
                    starstar = True
                    globs.append([])
                continue

            starstar = False
            if cls._is_glob(i):
                globs[-1].append(re.compile(fnmatch.translate(i)).match)
            else:
                assert i
                globs[-1].append(cls._match_string(i))

        # Make a list of the remaining *total* lengths for each run of globs.
        # This makes it easier to determine how much "wiggle room" we have for
        # a given run when there are multiple `**` patterns. See also the
        # `_match_glob_runs` method below.
        lengths = [len(i) for i in globs]
        for i in reversed(range(len(lengths) - 1)):
            lengths[i] += lengths[i + 1]
        return [cls._glob_run(i, j) for i, j in zip(globs, lengths)]

    @staticmethod
    def _match_string(s):
        return lambda x: x == s

    def _match_base(self, path, skip=False):
        base_bits = self.base.split()
        path_bits, next_bits = list_view(path.split()).split_at(len(base_bits))

        if not skip:
            # This code should only run when we have multiple `PathGlob`s for a
            # given filter.
            if path.root != self.base.root:
                return self.Result.no, next_bits

            for expected, actual in zip_longest(base_bits, path_bits):
                if actual is None:
                    # `path` is a parent of our pattern.
                    return self.Result.no, next_bits
                elif actual != expected:
                    # `path` diverges from our pattern, so no children of
                    # `path` could ever match.
                    return self.Result.never, next_bits

        return self.Result.yes, next_bits

    def _match_glob_run(self, run, path_bits, first=False):
        wanted_bits, next_bits = path_bits.split_at(len(run.matchers))
        for matcher, path_bit in zip_longest(run.matchers, wanted_bits):
            if path_bit is None:
                # `path` is a parent of our pattern.
                return self.Result.no, next_bits
            if not matcher(path_bit):
                # `path` diverges from our pattern, so no children of `path`
                # could ever match.
                result = self.Result.never if first else self.Result.no
                return result, next_bits

        return self.Result.yes, next_bits

    def _match_glob_runs(self, runs, path_bits):
        if len(runs) == 1:
            end_bits = path_bits[len(path_bits) - len(runs[0].matchers):]
            return self._match_glob_run(runs[0], end_bits)[0]

        # If there are still at least 2 glob runs left, the current run could
        # start anywhere so long as we have enough path components left to fit
        # all the runs.
        wiggle_room = len(path_bits) - runs[0].length
        for offset in range(wiggle_room + 1):
            result, bits = self._match_glob_run(runs[0], path_bits[offset:])
            if result:
                return self._match_glob_runs(runs[1:], bits)
        return self.Result.no

    def match(self, path, skip_base=False):
        result, path_bits = self._match_base(path, skip_base)
        if not result:
            return result

        glob = list_view(self.glob)
        result, path_bits = self._match_glob_run(glob[0], path_bits, True)
        if not result:
            return result

        if len(glob) > 1:
            result = self._match_glob_runs(glob[1:], path_bits)
            if not result:
                return result
        elif len(path_bits):
            # `path` is a child of our pattern, and we're not looking for
            # children.
            return self.Result.never

        # `path` matches our pattern. Check if it's the right file type.
        found_type = self.Type.dir if path.directory else self.Type.file
        if self.type & found_type:
            return self.Result.yes
        return self.Result.no


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
