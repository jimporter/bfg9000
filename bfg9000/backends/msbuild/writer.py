import os
import re

from ... import path
from ... import shell
from .solution import Solution, UuidMap
from .syntax import *  # noqa: F401
from ...versioning import Version


def executable(env=os.environ):
    return shell.which(env.get('MSBUILD', ['msbuild', 'xbuild']), env)


def version(env=os.environ):
    try:
        msbuild = executable(env)
        output = shell.execute(msbuild + ['/version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull, env=env)
        m = re.search(r'([\d\.]+)$', output)
        if m:
            return Version(m.group(1))
    except (IOError, OSError, shell.CalledProcessError):
        pass
    return None


priority = 1

_rule_handlers = {}
_post_rules = []


def rule_handler(*args):
    def decorator(fn):
        for i in args:
            _rule_handlers[i] = fn
        return fn
    return decorator


def post_rule(fn):
    _post_rules.append(fn)
    return fn


def write(env, build_inputs):
    uuids = UuidMap(env.builddir.append('.bfg_uuid').string())
    solution = Solution(uuids)

    for e in build_inputs.edges():
        _rule_handlers[type(e)](e, build_inputs, solution, env)
    for i in _post_rules:
        i(build_inputs, solution, env)

    sln_file = path.Path(build_inputs['project'].name + '.sln')
    with open(sln_file.string(env.base_dirs), 'w') as out:
        solution.write(out)
    for p in solution:
        os.makedirs(p.path.parent().string(env.base_dirs), exist_ok=True)
        with open(p.path.string(env.base_dirs), 'wb') as out:
            p.write(out)
    uuids.save()
