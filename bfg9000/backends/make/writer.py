import os
import re
import subprocess
from packaging.version import LegacyVersion

from ... import path
from .syntax import *
from ...iterutils import listify
from ...platforms import which


def version(env=os.environ):
    try:
        make = which(env.get('MAKE', ['make', 'gmake']), env)
        output = subprocess.check_output(
            [make, '--version'],
            universal_newlines=True
        )
        m = re.match(r'GNU Make ([\d\.]+)', output)
        if m:
            return LegacyVersion(m.group(1))
    except IOError:
        pass
    return None

priority = 2

_rule_handlers = {}
_pre_rules = []
_post_rules = []

dir_sentinel = '.dir'


def rule_handler(*args):
    def decorator(fn):
        for i in args:
            _rule_handlers[i] = fn
        return fn
    return decorator


def pre_rule(fn):
    _pre_rules.append(fn)
    return fn


def post_rule(fn):
    _post_rules.append(fn)
    return fn


def write(env, build_inputs):
    buildfile = Makefile(build_inputs.bfgpath.string(env.path_roots))
    buildfile.variable(path_vars[path.Root.srcdir], env.srcdir, Section.path)
    for i in path.InstallRoot:
        buildfile.variable(path_vars[i], env.install_dirs[i], Section.path)

    for i in _pre_rules:
        i(build_inputs, buildfile, env)
    for e in build_inputs.edges():
        _rule_handlers[type(e)](e, build_inputs, buildfile, env)
    for i in _post_rules:
        i(build_inputs, buildfile, env)

    with open(path.Path('Makefile').string(env.path_roots), 'w') as out:
        buildfile.write(out)


def cmd_var(cmd, buildfile):
    name = cmd.command_var.upper()
    return buildfile.variable(name, cmd.command, Section.command, True)


def flags_vars(name, value, buildfile):
    name = name.upper()
    gflags = buildfile.variable('GLOBAL_' + name, value, Section.flags, True)
    flags = buildfile.target_variable(name, gflags, True)
    return gflags, flags


def multitarget_rule(buildfile, targets, deps=None, order_only=None,
                     recipe=None, variables=None, phony=None):
    targets = listify(targets)
    if len(targets) > 1:
        primary = targets[0].path.addext('.stamp')
        buildfile.rule(target=targets, deps=[primary])
        recipe = listify(recipe) + [silent([ 'touch', var('@') ])]
    else:
        primary = targets[0]

    buildfile.rule(primary, deps, order_only, recipe, variables, phony)


@post_rule
def directory_rule(build_inputs, buildfile, env):
    mkdir_p = env.tool('mkdir_p')
    pattern = Pattern(os.path.join('%', dir_sentinel))
    path = Function('patsubst', pattern, Pattern('%'), var('@'), quoted=True)

    buildfile.rule(
        target=pattern,
        recipe=[
            silent(mkdir_p(cmd_var(mkdir_p, buildfile), path)),
            silent(['touch', qvar('@')])
        ]
    )
