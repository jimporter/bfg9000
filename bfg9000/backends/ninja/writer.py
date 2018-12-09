import os

from ... import iterutils
from ... import path
from ... import shell
from .syntax import *
from ...versioning import SpecifierSet, Version


def version(env=os.environ):
    try:
        ninja = shell.which(env.get('NINJA', ['ninja', 'ninja-build']), env)
        output = shell.execute(ninja + ['--version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull)
        return Version(output.strip())
    except (IOError, OSError, shell.CalledProcessError):
        pass
    return None


priority = 3
filepath = path.Path('build.ninja')

_rule_handlers = {}
_pre_rules = []
_post_rules = []


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
    buildfile = NinjaFile(build_inputs.bfgpath.string(env.base_dirs))
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
    gflags = buildfile.variable('global_' + name, value, Section.flags, True)
    flags = buildfile.variable(name, gflags, Section.other, True)
    return gflags, flags


def command_build(buildfile, env, output, inputs=None, implicit=None,
                  order_only=None, command=[], console=True, description=None):
    if console:
        rule_name = 'console_command'
        extra_implicit = ['PHONY']

        if not buildfile.has_rule('console_command'):
            extra_kwargs = {}
            if ( env.backend_version and env.backend_version in
                 SpecifierSet('>=1.5') ):
                extra_kwargs['pool'] = 'console'
            buildfile.rule(name='console_command',
                           command=shell.shell_list([var('cmd')]),
                           **extra_kwargs)

        if not buildfile.has_build('PHONY'):
            buildfile.build(output='PHONY', rule='phony')
    else:
        rule_name = 'command'
        extra_implicit = []

        if not buildfile.has_rule('command'):
            buildfile.rule(name='command',
                           command=shell.shell_list([var('cmd')]))

    variables = {'cmd': command}
    if description:
        variables['description'] = description
    buildfile.build(
        output=output,
        rule=rule_name,
        inputs=inputs,
        implicit=iterutils.listify(implicit) + extra_implicit,
        order_only=order_only,
        variables=variables
    )
