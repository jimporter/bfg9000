import os
import re
import subprocess

from .syntax import *
from ...makedirs import makedirs
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


def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator


def write(env, build_inputs):
    uuids = UuidMap(env.builddir.append('.bfg_uuid').string())
    solution = Solution(uuids)

    # TODO: Handle default().
    for e in build_inputs.edges:
        if type(e) in _rule_handlers:
            _rule_handlers[type(e)](e, build_inputs, solution, env)

    with open(env.builddir.append('project.sln').string(), 'w') as out:
        solution.write(out)
    for p in solution:
        projfile = env.builddir.append(p.path).string()
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
    uuids.save()
