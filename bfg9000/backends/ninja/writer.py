import os

from .. import BuildHook, BuildRuleHandler
from ... import iterutils
from ... import path
from ... import shell
from .syntax import *
from ...versioning import Version


def executable(env=os.environ):
    return shell.which(env.get('NINJA', ['ninja', 'ninja-build']), env)


def version(env=os.environ):
    try:
        ninja = executable(env)
        output = shell.execute(ninja + ['--version'], stdout=shell.Mode.pipe,
                               stderr=shell.Mode.devnull, env=env)
        return Version(output.strip())
    except (IOError, OSError, shell.CalledProcessError):
        pass
    return None


priority = 3
filepath = path.Path('build.ninja')

rule_handler = BuildRuleHandler()
pre_rules_hook = BuildHook()
post_rules_hook = BuildHook()


def write(env, build_inputs):
    buildfile = NinjaFile(build_inputs.bfgpath.string(env.base_dirs),
                          env.supports_destdir)
    buildfile.variable(buildfile.path_vars[path.Root.srcdir], env.srcdir,
                       Section.path)

    pre_rules_hook.run(build_inputs, buildfile, env)
    rule_handler.run(build_inputs.edges(), build_inputs, buildfile, env)
    post_rules_hook.run(build_inputs, buildfile, env)

    with open(filepath.string(env.base_dirs), 'w') as out:
        buildfile.write(out)


def flags_vars(name, value, buildfile):
    gflags = buildfile.variable('global_' + name, value, Section.flags, True)
    flags = buildfile.variable(name, gflags, Section.other, True)
    return gflags, flags


def command_build(buildfile, env, output, inputs=None, implicit=None,
                  order_only=None, command=[], console=False, phony=False,
                  description=None):
    if phony:
        extra_implicit = ['PHONY']
        if not buildfile.has_build('PHONY'):
            buildfile.build(output='PHONY', rule='phony')
    else:
        extra_implicit = []

    if console and features.supported('console', env.backend_version):
        rule_name = 'console_command'
        rule_kwargs = {'pool': 'console'}
    else:
        rule_name = 'command'
        rule_kwargs = {}

    if not buildfile.has_rule(rule_name):
        buildfile.rule(name=rule_name, command=shell.shell_list([var('cmd')]),
                       **rule_kwargs)

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
