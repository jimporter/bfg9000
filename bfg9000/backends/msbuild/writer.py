import os
import re

from .. import BuildHook, BuildRuleHandler
from ... import path
from ... import shell
from .solution import Solution, UuidMap
from .syntax import *  # noqa: F401
from ...versioning import Version


def executable(env=os.environ):
    return shell.which(env.get('MSBUILD', ['msbuild', 'xbuild']), env=env)


def version(env=os.environ):
    try:
        msbuild = executable(env)
        output = shell.execute(msbuild + ['/version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull, env=env)
        m = re.search(r'([\d\.]+)$', output)
        if m:
            return Version(m.group(1))
    except (OSError, shell.CalledProcessError):
        pass
    return None


priority = 1

rule_handler = BuildRuleHandler()
pre_rules_hook = BuildHook()
post_rules_hook = BuildHook()


def write(env, build_inputs):
    uuids = UuidMap(env.builddir.append('.bfg_uuid').string())
    solution = Solution(uuids)

    pre_rules_hook.run(build_inputs, solution, env)
    rule_handler.run(build_inputs.edges(), build_inputs, solution, env)
    post_rules_hook.run(build_inputs, solution, env)

    sln_file = path.Path(build_inputs['project'].name + '.sln')
    with open(sln_file.string(env.base_dirs), 'w') as out:
        solution.write(out)
    for p in solution:
        os.makedirs(p.path.parent().string(env.base_dirs), exist_ok=True)
        with open(p.path.string(env.base_dirs), 'wb') as out:
            p.write(out)
    uuids.save()
