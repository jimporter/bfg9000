import os
import re

from ... import path
from ... import shell
from .syntax import *
from ...iterutils import listify
from ...versioning import Version


def version(env=os.environ):
    try:
        make = shell.which(env.get('MAKE', ['make', 'gmake']), env)
        output = shell.execute(make + ['--version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull)
        m = re.match(r'GNU Make ([\d\.]+)', output)
        if m:
            return Version(m.group(1))
    except (IOError, OSError, shell.CalledProcessError):
        pass
    return None


priority = 2
filepath = path.Path('Makefile')

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
    buildfile = Makefile(build_inputs.bfgpath.string(env.base_dirs))
    buildfile.variable(path_vars[path.Root.srcdir], env.srcdir, Section.path)

    for i in _pre_rules:
        i(build_inputs, buildfile, env)
    for e in build_inputs.edges():
        _rule_handlers[type(e)](e, build_inputs, buildfile, env)
    for i in _post_rules:
        i(build_inputs, buildfile, env)

    with open(filepath.string(env.base_dirs), 'w') as out:
        buildfile.write(out)


def flags_vars(name, value, buildfile):
    name = name.upper()
    gflags = buildfile.variable('GLOBAL_' + name, value, Section.flags, True)
    flags = buildfile.target_variable(name, gflags, True)
    return gflags, flags


def multitarget_rule(buildfile, targets, deps=None, order_only=None,
                     recipe=None, variables=None, phony=None):
    targets = listify(targets)
    if len(targets) > 1:
        first = targets[0]
        first_path = first if isinstance(first, path.Path) else first.path
        primary = first_path.addext('.stamp')
        buildfile.rule(target=targets, deps=[primary])
        recipe = listify(recipe) + [Silent([ 'touch', var('@') ])]
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
            Silent(mkdir_p(path)),
            Silent(['touch', qvar('@')])
        ]
    )
