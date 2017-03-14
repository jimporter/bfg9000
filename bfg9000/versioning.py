import platform
import re
from itertools import chain
from packaging.specifiers import (
    LegacySpecifier as Specifier, Specifier as PythonSpecifier,
    SpecifierSet as PythonSpecifierSet
)
from packaging.version import (
    Version as PythonVersion, LegacyVersion as Version
)

from .app_version import version as bfg_version
from .iterutils import iterate

bfg_version = PythonVersion(bfg_version)
python_version = PythonVersion(platform.python_version())


# Use a LegacySpecifierSet instead once packaging.specifiers has it. See
# <https://github.com/pypa/packaging/pull/92>.
class SpecifierSet(PythonSpecifierSet):
    def __init__(self, specifiers=''):
        specifiers = [s.strip() for s in specifiers.split(',') if s.strip()]
        parsed = set()
        for specifier in specifiers:
            parsed.add(Specifier(specifier))
        self._specs = frozenset(parsed)
        self._prereleases = None


def simplify_specifiers(spec):
    """Try to simplify a SpecifierSet by combining redundant specifiers."""

    def key(s):
        return (s.version, 1 if s.operator in ['>=', '<'] else 2)

    def in_bounds(v, lo, hi):
        if lo and v not in lo:
            return False
        if hi and v not in hi:
            return False
        return True

    def err():
        return ValueError('inconsistent specifier set {}'.format(spec))

    gt = None
    lt = None
    eq = None
    ne = []

    for i in spec:
        if i.operator == '==':
            if eq is None:
                eq = i
            elif eq != i:
                raise err()
        elif i.operator == '!=':
            ne.append(i)
        elif i.operator in ['>', '>=']:
            gt = i if gt is None else max(gt, i, key=key)
        elif i.operator in ['<', '<=']:
            lt = i if lt is None else min(lt, i, key=key)
        else:
            raise err()

    ne = [i for i in ne if in_bounds(i.version, gt, lt)]
    if eq:
        if ( any(i.version in eq for i in ne) or
             not in_bounds(eq.version, gt, lt)):
            raise err()
        return SpecifierSet(str(eq))
    if lt and gt:
        if lt.version not in gt or gt.version not in lt:
            raise err()
        if ( gt.version == lt.version and gt.operator == '>=' and
             lt.operator == '<='):
            return SpecifierSet('=={}'.format(gt.version))

    return SpecifierSet(
        ','.join(str(i) for i in chain(iterate(gt), iterate(lt), ne))
    )


def check_version(version, specifier, kind):
    msg = "{kind} version {ver} doesn't meet requirement {req}"
    if version not in specifier:
        raise ValueError(msg.format(kind=kind, ver=version, req=specifier))


def detect_version(string):
    m = re.search(r'(\d+(?:\.\d+)+)', string)
    return Version(m.group(1)) if m else None
