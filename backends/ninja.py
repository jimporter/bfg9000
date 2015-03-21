import os
import re
import sys
from collections import OrderedDict, namedtuple
from itertools import chain

import toolchains.cc
import languages

cc = toolchains.cc.CcCompiler() # TODO: make this replaceable

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

NinjaRule = namedtuple('NinjaRule', ['command', 'depfile'])
NinjaBuild = namedtuple('NinjaBuild', ['rule', 'inputs', 'implicit',
                                       'variables'])
class NinjaVariable(object):
    def __init__(self, name):
        self.name = re.sub('/', '_', name)

    def use(self):
        return '${}'.format(self.name)

    def __str__(self):
        return self.name

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

    def variable(self, name, value):
        if not isinstance(name, NinjaVariable):
            name = NinjaVariable(name)
        if self.has_variable(name):
            raise RuntimeError('variable "{}" already exists'.format(name))
        self._variables[name] = value

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

    def build(self, output, rule, inputs=None, implicit=None, variables=None):
        if self.has_build(output):
            raise RuntimeError('build for "{}" already exists'.format(output))
        self._builds[output] = NinjaBuild(rule, inputs, implicit, variables)

    def has_build(self, name):
        return name in self._builds

    def _write_variable(self, out, name, value, indent=0):
        out.write('{indent}{name} = {value}\n'.format(
            indent='  ' * indent, name=name, value=value
        ))

    def _write_rule(self, out, name, command, depfile):
        out.write('rule {}\n'.format(name))
        self._write_variable(out, 'command', command, 1)
        if depfile:
            self._write_variable(out, 'depfile', depfile, 1)

    def _write_build(self, out, name, rule, inputs, implicit, variables):
        out.write('build {output}: {rule}'.format(output=name, rule=rule))

        for i in inputs or []:
            out.write(' ' + i)

        first = True
        for i in implicit or []:
            if first:
                first = False
                out.write(' |')
            out.write(' ' + i)

        out.write('\n')

        if variables:
            for k, v in variables.iteritems():
                self._write_variable(out, k, v, 1)

    def write(self, out):
        for name, value in self._variables.iteritems():
            self._write_variable(out, name, value)
        if self._variables:
            out.write('\n')

        for name, rule in self._rules.iteritems():
            self._write_rule(out, name, *rule)
            out.write('\n')

        for name, build in self._builds.iteritems():
            self._write_build(out, name, *build)

def write(path, targets):
    writer = NinjaWriter()
    for rule in targets:
        __rule_handlers__[rule.kind](writer, rule)
    with open(os.path.join(path, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(writer, lang):
    cmd, varname = cc.command_name(lang)
    var = NinjaVariable(varname)
    if not writer.has_variable(var):
        writer.variable(var, cmd)
    return var

@rule_handler('object_file')
def emit_object_file(writer, rule):
    cmd = cmd_var(writer, rule['lang'])
    rulename = str(cmd)
    cflags = NinjaVariable('{}flags'.format(cmd))

    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc.compile_command(
            cmd=cmd.use(), input='$in', output='$out', dep='$out.d',
            prevars=cflags.use()
        ), depfile='$out.d')

    variables = {}
    if rule['options']:
        variables[cflags] = rule['options']

    writer.build(output=toolchains.cc.target_name(rule), rule=rulename,
                 inputs=[toolchains.cc.target_name(rule['file'])],
                 variables=variables)

def emit_link(writer, rule, rulename):
    lang = languages.lang(rule['files'])
    cmd = cmd_var(writer, lang)
    cflags = NinjaVariable('{}flags'.format(cmd))
    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc.link_command(
            cmd=cmd.use(), mode=rule.kind, input=['$in'],
            libs=None, prevars=cflags.use(), postvars='$libs $ldflags',
            output='$out'
        ))

    variables = {}
    if rule['libs']:
        variables['libs'] = cc.link_libs(rule['libs'])
    if rule['compile_options']:
        variables[cflags] = rule['compile_options']
    if rule['link_options']:
        variables['ldflags'] = rule['link_options']

    writer.build(
        output=toolchains.cc.target_name(rule), rule=rulename,
        inputs=(toolchains.cc.target_name(i) for i in rule['files']),
        implicit=(toolchains.cc.target_name(i) for i in rule['libs']
                  if i.kind != 'external_library'),
        variables=variables
    )

@rule_handler('executable')
def emit_executable(writer, rule):
    emit_link(writer, rule, 'link')

@rule_handler('library')
def emit_library(writer, rule):
    emit_link(writer, rule, 'linklib')

@rule_handler('alias')
def emit_alias(writer, rule):
    writer.build(
        output=toolchains.cc.target_name(rule), rule='phony',
        inputs=(toolchains.cc.target_name(i) for i in rule.deps)
    )

@rule_handler('command')
def emit_command(writer, rule):
    if not writer.has_rule('command'):
        writer.rule(name='command', command='$cmd')
        writer.build(
            output=rule.name, rule='command',
            inputs=(toolchains.cc.target_name(i) for i in rule.deps),
            variables={'cmd': ' && '.join(rule['cmd'])}
        )
