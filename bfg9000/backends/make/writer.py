import os
import re

from .. import BuildHook, BuildRuleHandler
from ... import file_types, path, shell
from .syntax import *
from ...iterutils import listify, uniques
from ...versioning import Version


def executable(env=os.environ):
    return shell.which(env.get('MAKE', ['make', 'gmake']), env)


def version(env=os.environ):
    try:
        make = executable(env)
        output = shell.execute(make + ['--version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull, env=env)
        m = re.match(r'GNU Make ([\d\.]+)', output)
        if m:
            return Version(m.group(1))
    except (IOError, OSError, shell.CalledProcessError):
        pass
    return None


priority = 2
filepath = path.Path('Makefile')
dir_sentinel = '.dir'

rule_handler = BuildRuleHandler()
pre_rules_hook = BuildHook()
post_rules_hook = BuildHook()


def write(env, build_inputs):
    buildfile = Makefile(build_inputs.bfgpath.string(env.base_dirs),
                         env.supports_destdir,
                         gnu=env.backend_version is not None)
    buildfile.variable(buildfile.path_vars[path.Root.srcdir], env.srcdir,
                       Section.path)

    pre_rules_hook.run(build_inputs, buildfile, env)
    rule_handler.run(build_inputs.edges(), build_inputs, buildfile, env)
    post_rules_hook.run(build_inputs, buildfile, env)

    with open(filepath.string(env.base_dirs), 'w') as out:
        buildfile.write(out)


def flags_vars(name, value, buildfile):
    name = name.upper()
    gflags = buildfile.variable('GLOBAL_' + name, value, Section.flags, True)
    flags = buildfile.target_variable(name, gflags, True)
    return gflags, flags


def _get_path(thing):
    return thing if isinstance(thing, path.Path) else thing.path


def multitarget_rule(build_inputs, buildfile, targets, deps=None,
                     order_only=None, recipe=None, variables=None, phony=None,
                     clean_stamp=True):
    targets = listify(targets)
    if len(targets) > 1:
        first = targets[0]
        primary = _get_path(first).addext('.stamp')
        buildfile.rule(target=targets, deps=[primary])
        recipe = listify(recipe) + [Silent([ 'touch', qvar('@') ])]
        if clean_stamp:
            build_inputs.add_target(file_types.File(primary))
    else:
        primary = targets[0]

    buildfile.rule(primary, deps, order_only, recipe, variables, phony)


def directory_deps(targets):
    builddir = path.Path('.')
    dirs = uniques(_get_path(i).parent() for i in targets)
    return [i.append(dir_sentinel) for i in dirs if i != builddir]


@post_rules_hook
def directory_rule(build_inputs, buildfile, env):
    mkdir_p = env.tool('mkdir_p')
    pattern = Pattern(os.path.join('%', dir_sentinel))
    path = Function('patsubst', pattern, Pattern('%'), var('@'), quoted=True)

    buildfile.rule(
        target=pattern,
        recipe=[
            Silent(mkdir_p(path)),
            Silent(['touch', qvar('@')])
        ]
    )
