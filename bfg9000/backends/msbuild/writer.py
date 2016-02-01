import os
import re
import subprocess
from packaging.version import Version

from .syntax import *
from ...pathutils import makedirs
from ...platforms import which


def version(env=os.environ):
    try:
        msbuild = which(env.get('MSBUILD', ['msbuild', 'xbuild']), env)
        output = subprocess.check_output(
            [msbuild, '/version'],
            universal_newlines=True
        )
        m = re.search(r'([\d\.]+)$', output)
        if m:
            return Version(m.group(1))
    except IOError:
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

    for e in build_inputs.edges:
        _rule_handlers[type(e)](e, build_inputs, solution, env)

    # XXX: Handle default builds. Default builds go first in the solution. This
    # also means we'd need to support aliases so that we can have multiple
    # builds be the default.
    with open(env.builddir.append('project.sln').string(), 'w') as out:
        solution.write(out)
    for p in solution:
        projfile = env.builddir.append(p.path).string()
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
    uuids.save()
