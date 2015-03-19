import cStringIO
import os
import sys
from collections import OrderedDict
from itertools import chain

import cc_toolchain
import languages

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

def rule_name(name):
    if name == 'c++':
        return 'cxx'
    return name

def use_var(name):
    return '${}'.format(name)

class NinjaWriter(object):
    def __init__(self):
        self._variables = OrderedDict()
        self._rules = OrderedDict()
        self._builds = []

    def _write_variable(self, out, name, value, indent=0):
        out.write('{indent}{name} = {value}\n'.format(
            indent='  ' * indent, name=name, value=value
        ))

    def variable(self, name, value):
        if self.has_variable(name):
            raise RuntimeError('variable "{}" already exists'.format(name))
        out = cStringIO.StringIO()
        self._write_variable(out, name, value)
        self._variables[name] = out.getvalue()

    def has_variable(self, name):
        return name in self._variables

    def rule(self, name, command, depfile=None):
        if self.has_rule(name):
            raise RuntimeError('rule "{}" already exists'.format(name))
        out = cStringIO.StringIO()
        out.write('rule {}\n'.format(name))
        self._write_variable(out, 'command', command, 1)
        if depfile:
            self._write_variable(out, 'depfile', depfile, 1)
        self._rules[name] = out.getvalue()

    def has_rule(self, name):
        return name in self._rules

    def build(self, output, rule, inputs=None, implicit=None, variables=None):
        out = cStringIO.StringIO()
        out.write('build {output}: {rule}'.format(output=output, rule=rule))

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
        self._builds.append(out.getvalue())

    def write(self, out):
        for v in self._variables.itervalues():
            out.write(v)
        if self._variables:
            out.write('\n')

        for r in self._rules.itervalues():
            out.write(r)
            out.write('\n')

        for b in self._builds:
            out.write(b)

def write(path, targets):
    writer = NinjaWriter()
    for rule in targets:
        __rule_handlers__[rule.kind](writer, rule)
    with open(os.path.join(path, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(writer, lang):
    var = rule_name(lang).upper()
    if not writer.has_variable(var):
        writer.variable(var, cc_toolchain.command_name(lang))
    return var

@rule_handler('object_file')
def emit_object_file(writer, rule):
    cmd = cmd_var(writer, rule['lang'])
    rulename = rule_name(rule['lang'])
    cflags = '{}flags'.format(rulename)

    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc_toolchain.compile_command(
            cmd=use_var(cmd), input='$in', output='$out', dep='$out.d',
            prevars='$' + cflags
        ), depfile='$out.d')

    variables = {}
    if rule['options']:
        variables[cflags] = rule['options']

    writer.build(output=cc_toolchain.target_name(rule), rule=rulename,
                 inputs=[cc_toolchain.target_name(rule['file'])],
                 variables=variables)

def emit_link(writer, rule, rulename):
    lang = languages.lang(rule['files'])
    cmd = cmd_var(writer, lang)
    cflags = '{}flags'.format(rule_name(lang))
    if not writer.has_rule(rulename):
        writer.rule(name=rulename, command=cc_toolchain.link_command(
            cmd=use_var(cmd), mode=rule.kind, input=['$in'],
            libs=None, prevars='$' + cflags, postvars='$libs $ldflags',
            output='$out'
        ))

    variables = {}
    if rule['libs']:
        variables['libs'] = cc_toolchain.link_libs(rule['libs'])
    if rule['compile_options']:
        variables[cflags] = rule['compile_options']
    if rule['link_options']:
        variables['ldflags'] = rule['link_options']

    writer.build(
        output=cc_toolchain.target_name(rule), rule=rulename,
        inputs=(cc_toolchain.target_name(i) for i in rule['files']),
        implicit=(cc_toolchain.target_name(i) for i in rule['libs']
                  if i.kind != 'external_library'),
        variables=variables
    )

@rule_handler('executable')
def emit_executable(writer, rule):
    emit_link(writer, rule, 'link')

@rule_handler('library')
def emit_library(writer, rule):
    emit_link(writer, rule, 'linklib')

@rule_handler('target')
def emit_target(writer, rule):
    writer.build(
        output=cc_toolchain.target_name(rule), rule='phony',
        inputs=(cc_toolchain.target_name(i) for i in rule.deps)
    )

@rule_handler('command')
def emit_command(writer, rule):
    if not writer.has_rule('command'):
        writer.rule(name='command', command='$cmd')
        writer.build(
            output=rule.name, rule='command',
            inputs=(cc_toolchain.target_name(i) for i in rule.deps),
            variables={'cmd': ' && '.join(rule['cmd'])}
        )
