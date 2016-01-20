import os
import subprocess
from itertools import chain
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from six.moves import cStringIO as StringIO

from ... import iterutils
from ... import path
from ... import safe_str
from ... import shell
from .syntax import *
from ...platforms import platform_name, which


def version(env=os.environ):
    try:
        ninja = which(env.get('NINJA', ['ninja', 'ninja-build']), env)
        output = subprocess.check_output(
            [ninja, '--version'],
            universal_newlines=True
        )
        return Version(output.strip())
    except IOError:
        return None

priority = 3

_rule_handlers = {}
_pre_rules = []
_post_rules = []


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
    buildfile = NinjaFile()
    buildfile.variable(path_vars[path.Root.srcdir], env.srcdir, Section.path)
    for i in path.InstallRoot:
        buildfile.variable(path_vars[i], env.install_dirs[i], Section.path)

    for i in _pre_rules:
        i(build_inputs, buildfile, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e)](e, build_inputs, buildfile, env)
    for i in _post_rules:
        i(build_inputs, buildfile, env)

    with open(env.builddir.append('build.ninja').string(), 'w') as out:
        buildfile.write(out)


def cmd_var(cmd, buildfile):
    name = cmd.command_var
    return buildfile.variable(name, cmd.command, Section.command, True)


def flags_vars(name, value, buildfile):
    gflags = buildfile.variable('global_' + name, value, Section.flags, True)
    flags = buildfile.variable(name, gflags, Section.other, True)
    return gflags, flags


class Commands(object):
    def __init__(self, commands, environ=None):
        self.commands = iterutils.listify(commands)
        self.environ = environ or {}

    def use(self):
        out = Writer(StringIO())
        if self.__needs_shell and platform_name() == 'windows':
            out.write_literal('cmd /c ')

        env_vars = shell.global_env(self.environ)
        for line in shell.join_commands(chain(env_vars, self.commands)):
            out.write_shell(line)
        return safe_str.escaped_str(out.stream.getvalue())

    def _safe_str(self):
        return self.use()

    @property
    def __needs_shell(self):
        return (
            len(self.commands) + len(self.environ) > 1 or
            any(not iterutils.isiterable(i) for i in self.commands)
        )


def command_build(buildfile, env, output, inputs=None, implicit=None,
                  order_only=None, commands=None, environ=None):
    extra_kwargs = {}
    if env.backend_version in SpecifierSet('>=1.5'):
        extra_kwargs['pool'] = 'console'

    if not buildfile.has_rule('command'):
        buildfile.rule(name='command', command=var('cmd'), **extra_kwargs)
    if not buildfile.has_build('PHONY'):
        buildfile.build(output='PHONY', rule='phony')

    buildfile.build(
        output=output,
        rule='command',
        inputs=inputs,
        implicit=iterutils.listify(implicit) + ['PHONY'],
        order_only=order_only,
        variables={'cmd': Commands(commands, environ)}
    )
