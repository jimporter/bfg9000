import os
import re
import subprocess
from packaging.version import LegacyVersion

from ... import path
from .syntax import *


def version(env=os.environ):
    with open(os.devnull, 'wb') as devnull:
        try:
            msbuild = path.which(env.get('MSBUILD', ['msbuild', 'xbuild']),
                                 env, first_word=True)
            output = subprocess.check_output(
                '{} /version'.format(msbuild),
                shell=True, universal_newlines=True, stderr=devnull
            )
            m = re.search(r'([\d\.]+)$', output)
            if m:
                return LegacyVersion(m.group(1))
        except IOError:
            pass
    return None


priority = 1

_rule_handlers = {}


def rule_handler(*args):
    def decorator(fn):
        for i in args:
            _rule_handlers[i] = fn
        return fn
    return decorator


def write(env, build_inputs):
    uuids = UuidMap(env.builddir.append('.bfg_uuid').string())
    solution = Solution(uuids)

    for e in build_inputs.edges():
        _rule_handlers[type(e)](e, build_inputs, solution, env)

    # XXX: Handle default builds. Default builds go first in the solution. This
    # also means we'd need to support aliases so that we can have multiple
    # builds be the default.
    sln_file = path.Path(build_inputs['project'].name + '.sln')
    with open(sln_file.string(env.path_roots), 'w') as out:
        solution.write(out)
    for p in solution:
        path.makedirs(p.path.parent().string(env.path_roots), exist_ok=True)
        with open(p.path.string(env.path_roots), 'w') as out:
            p.write(out)
    uuids.save()
