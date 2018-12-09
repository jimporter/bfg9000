import os
import re

from ... import path
from ... import shell
from .syntax import *
from ...versioning import Version


def version(env=os.environ):
    try:
        msbuild = shell.which(env.get('MSBUILD', ['msbuild', 'xbuild']), env)
        output = shell.execute(msbuild + ['/version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull)
        m = re.search(r'([\d\.]+)$', output)
        if m:
            return Version(m.group(1))
    except (IOError, OSError, shell.CalledProcessError):
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
    with open(sln_file.string(env.base_dirs), 'w') as out:
        solution.write(out)
    for p in solution:
        path.makedirs(p.path.parent().string(env.base_dirs), exist_ok=True)
        with open(p.path.string(env.base_dirs), 'w') as out:
            p.write(out)
    uuids.save()
