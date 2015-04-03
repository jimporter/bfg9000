import os
import re
import sys
from collections import OrderedDict, namedtuple
from itertools import chain

import toolchains.cc

cc = toolchains.cc.CcCompiler() # TODO: make this replaceable

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

NinjaRule = namedtuple('NinjaRule', ['command', 'depfile'])
NinjaBuild = namedtuple('NinjaBuild', ['rule', 'inputs', 'implicit',
                                       'order_only', 'variables'])
class NinjaVariable(object):
    def __init__(self, name):
        self.name = re.sub('/', '_', name)

    def use(self):
        return '${}'.format(self.name)

    def __str__(self):
        return self.use()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __ne__(self, rhs):
        return self.name != rhs.name

class NinjaWriter(object):
    def __init__(self):
        self._variables = OrderedDict()
        self._rules = OrderedDict()
        self._builds = OrderedDict()
        self._defaults = []

    def variable(self, name, value):
        if not isinstance(name, NinjaVariable):
            name = NinjaVariable(name)
        if self.has_variable(name):
            raise RuntimeError('variable "{}" already exists'.format(name))
        self._variables[name] = value
        return name

    def has_variable(self, name):
        if not isinstance(name, NinjaVariable):
            name = NinjaVariable(name)
        return name in self._variables

    def rule(self, name, command, depfile=None):
        if self.has_rule(name):
            raise RuntimeError('rule "{}" already exists'.format(name))
        self._rules[name] = NinjaRule(command, depfile)

    def has_rule(self, name):
        return name in self._rules

    def build(self, output, rule, inputs=None, implicit=None, order_only=None,
              variables=None):
        real_variables = {}
        if variables:
            for k, v in variables.iteritems():
                if not isinstance(k, NinjaVariable):
                    k = NinjaVariable(k)
                real_variables[k] = v

        if self.has_build(output):
            raise RuntimeError('build for "{}" already exists'.format(output))
        self._builds[output] = NinjaBuild(rule, inputs, implicit, order_only,
                                          real_variables)

    def default(self, paths):
        self._defaults.extend(paths)

    def has_build(self, name):
        return name in self._builds

    def _write_variable(self, out, name, value, indent=0):
        out.write('{indent}{name} = {value}\n'.format(
            indent='  ' * indent, name=name.name, value=value
        ))

    def _write_rule(self, out, name, rule):
        out.write('rule {}\n'.format(name))
        self._write_variable(out, NinjaVariable('command'), rule.command, 1)
        if rule.depfile:
            self._write_variable(out, NinjaVariable('depfile'), rule.depfile, 1)

    def _write_build(self, out, name, build):
        out.write('build {output}: {rule}'.format(output=name, rule=build.rule))

        for i in build.inputs or []:
            out.write(' ' + i)

        first = True
        for i in build.implicit or []:
            if first:
                first = False
                out.write(' |')
            out.write(' ' + i)

        first = True
        for i in build.order_only or []:
            if first:
                first = False
                out.write(' ||')
            out.write(' ' + i)

        out.write('\n')

        if build.variables:
            for k, v in build.variables.iteritems():
                self._write_variable(out, k, v, 1)

    def write(self, out):
        for name, value in self._variables.iteritems():
            self._write_variable(out, name, value)
        if self._variables:
            out.write('\n')

        for name, rule in self._rules.iteritems():
            self._write_rule(out, name, rule)
            out.write('\n')

        for name, build in self._builds.iteritems():
            self._write_build(out, name, build)

        if self._defaults:
            out.write('\ndefault {}\n'.format(' '.join(self._defaults)))

def write(env, build_inputs):
    writer = NinjaWriter()
    srcdir_var = writer.variable('srcdir', env.srcdir)
    env.set_srcdir_var(srcdir_var)

    writer.default(env.target_path(i) for i in build_inputs.default_targets)
    for e in build_inputs.edges:
        __rule_handlers__[type(e).__name__](e, writer, env)

    with open(os.path.join(env.builddir, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(writer, lang):
    cmd, varname = cc.command_name(lang)
    var = NinjaVariable(varname)
    if not writer.has_variable(var):
        writer.variable(var, cmd)
    return var

@rule_handler('Compile')
def emit_object_file(rule, writer, env):
    cmd = cmd_var(writer, rule.file.lang)
    rulename = cmd.name
    cflags = NinjaVariable('{}flags'.format(cmd.name))

    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc.compile_command(
            cmd=cmd, input='$in', output='$out', dep='$out.d',
            prevars=cflags
        ), depfile='$out.d')

    variables = {}
    cflags_value = []
    if rule.target.in_library:
        cflags_value.append(cc.library_flag())
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)

    writer.build(output=env.target_name(rule.target), rule=rulename,
                 inputs=[env.target_path(rule.file)],
                 variables=variables)

@rule_handler('Link')
def emit_link(rule, writer, env):
    cmd = cmd_var(writer, (i.lang for i in rule.files))

    if type(rule.target).__name__ == 'Library':
        rulename = '{}_linklib'.format(cmd.name)
        mode = 'library'
    else:
        rulename = '{}_link'.format(cmd.name)
        mode = 'executable'

    cflags = NinjaVariable('{}flags'.format(cmd.name))
    libs_var = NinjaVariable('libs')
    ldflags = NinjaVariable('ldflags')

    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc.link_command(
            cmd=cmd, mode=mode, input='$in', output='$out',
            prevars=cflags, postvars=[libs_var, ldflags]
        ))

    variables = {}
    if rule.libs:
        variables[libs_var] = cc.link_libs(rule.libs)
    if rule.compile_options:
        variables[cflags] = rule.compile_options
    if rule.link_options:
        variables[ldflags] = rule.link_options

    writer.build(
        output=env.target_name(rule.target), rule=rulename,
        inputs=(env.target_path(i) for i in rule.files),
        implicit=(env.target_path(i) for i in rule.libs if not i.is_source),
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, writer, env):
    writer.build(
        output=env.target_name(rule.target), rule='phony',
        inputs=[env.target_path(i) for i in rule.deps]
    )

@rule_handler('Command')
def emit_command(rule, writer, env):
    if not writer.has_rule('command'):
        writer.rule(name='command', command='$cmd')
        writer.build(
            output=env.target_name(rule.target), rule='command',
            inputs=(env.target_path(i) for i in rule.deps),
            variables={'cmd': ' && '.join(rule.cmd)}
        )
