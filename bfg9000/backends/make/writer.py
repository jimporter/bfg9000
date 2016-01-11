import os
import re
import subprocess
from packaging.version import Version

from ... import path
from .syntax import *
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
            return Version(m.group(1))
    except IOError:
        pass
    return None

priority = 2

_rule_handlers = {}
_pre_rules = []
_post_rules = []

dir_sentinel = '.dir'


def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator


def pre_rule(fn):
    _pre_rules.append(fn)
    return fn


def post_rule(fn):
    _post_rules.append(fn)
    return fn


def write(env, build_inputs):
    buildfile = Makefile()
    buildfile.variable(path_vars[path.Root.srcdir], env.srcdir, Section.path)
    for i in path.InstallRoot:
        buildfile.variable(path_vars[i], env.install_dirs[i], Section.path)

    for i in _pre_rules:
        i(build_inputs, buildfile, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e)](e, build_inputs, buildfile, env)
    for i in _post_rules:
        i(build_inputs, buildfile, env)

    with open(env.builddir.append('Makefile').string(), 'w') as out:
        buildfile.write(out)


def cmd_var(cmd, buildfile):
    name = cmd.command_var.upper()
    return buildfile.variable(name, cmd.command, Section.command, True)


def flags_vars(name, value, buildfile):
    name = name.upper()
    gflags = buildfile.variable('GLOBAL_' + name, value, Section.flags, True)
    flags = buildfile.target_variable(name, gflags, True)
    return gflags, flags


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
