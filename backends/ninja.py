import cc_toolchain
import cStringIO
import os
import sys
from collections import OrderedDict

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

class NinjaWriter(object):
    def __init__(self):
        self._rules = OrderedDict()
        self._builds = []

    def _write_variable(self, out, name, value, indent=0):
        out.write('{indent}{name} = {value}\n'.format(
            indent='  ' * indent, name=name, value=value
        ))

    def rule(self, name, command, depfile=None):
        if self.has_rule(name):
            raise RuntimeError('rule "{}" already exists'.format(name))
        out = cStringIO.StringIO()
        out.write('rule {}\n'.format(name))
        out.write('  command = {}\n'.format(command))
        if depfile:
            self._write_variable(out, 'depfile', depfile, 1)
        self._rules[name] = out.getvalue()

    def has_rule(self, name):
        return name in self._rules

    def build(self, output, rule, inputs=None, variables=None):
        out = cStringIO.StringIO()
        out.write('build {output}: {rule} {inputs}\n'.format(
            output=output, rule=rule, inputs=' '.join(inputs or [])
        ))
        if variables:
            for k, v in variables.iteritems():
                self._write_variable(out, k, v, 1)
        self._builds.append(out.getvalue())

    def write(self, out):
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

@rule_handler('object_file')
def __emit_object_file__(writer, rule):
    rulename = 'cxx' # TODO
    if not writer.has_rule(rulename):
        writer.rule(rulename, cc_toolchain.compile_command(
            lang=rule.attrs['lang'], input='$in', output='$out',
            dep='$out.d'
        ), depfile='$out.d')
    writer.build(cc_toolchain.target_name(rule), 'cxx',
                 [rule.attrs['file']])

def __emit_link__(writer, rule, rulename):
    if not writer.has_rule(rulename):
        writer.rule(rulename, cc_toolchain.link_command(
            lang='c++', mode=rule.kind, input='$in', libs=None,
            postvars='$libs', output='$out'
        ))

    variables = {}
    if rule.attrs['libs']:
        variables['libs'] = cc_toolchain.link_libs(rule.attrs['libs'])
    writer.build(
        cc_toolchain.target_name(rule), rulename,
        (cc_toolchain.target_name(i) for i in rule.attrs['files']),
        variables=variables
    )

@rule_handler('executable')
def __emit_executable__(writer, rule):
    __emit_link__(writer, rule, 'link')

@rule_handler('library')
def __emit_library__(writer, rule):
    __emit_link__(writer, rule, 'link')

@rule_handler('target')
def __emit_target__(writer, rule):
    writer.build(
        cc_toolchain.target_name(rule), 'phony',
        (cc_toolchain.target_name(i) for i in rule.deps)
    )

@rule_handler('command')
def __emit_command__(writer, rule):
    if not writer.has_rule('command'):
        writer.rule('command', '$cmd')
        writer.build(rule.name, 'command', variables={
            'cmd': ' && '.join(rule.attrs['cmd'])
        })
