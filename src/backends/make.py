import os
import re
from collections import OrderedDict, namedtuple
from itertools import chain

import toolchains.cc
from builtin_rules import ObjectFile
from languages import ext2lang
from platform import target_name

cc = toolchains.cc.CcCompiler() # TODO: make this replaceable

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['target', 'deps', 'recipe', 'variables',
                                   'phony'])

class MakeVariable(object):
    def __init__(self, name):
        self.name = re.sub('/', '_', name).upper()

    def use(self):
        return '$({})'.format(self.name)

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __ne__(self, rhs):
        return self.name != rhs.name

class MakeWriter(object):
    def __init__(self):
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict()
        self._includes = []
        self._rules = []

    def variable(self, name, value, target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if self.has_variable(name, target=target):
            raise RuntimeError('variable "{}" already exists'.format(name))

        if target:
            self._target_variables[(target, name)] = value
        else:
            self._global_variables[name] = value
        return name

    def has_variable(self, name, target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if target:
            return (target, name) in self._target_variables
        else:
            return name in self._global_variables

    def include(self, name, optional=False):
        self._includes.append(MakeInclude(name, optional))

    def rule(self, target, deps, recipe, variables=None, phony=False):
        self._rules.append(MakeRule(target, deps, recipe, variables, phony))

    def _write_variable(self, out, name, value, target=None):
        if target:
            out.write('{}: '.format(target))
        out.write('{name} := {value}\n'.format(
            name=name, value=value
        ))

    def _write_rule(self, out, target, deps, recipe, variables, phony):
        if variables:
            for name, value in variables.iteritems():
                self._write_variable(out, name, value, target=target)
        if phony:
            out.write('.PHONY: {}\n'.format(target))
        out.write('{target}:{deps}\n'.format(
            target=target,
            deps=''.join(' ' + i for i in deps)
        ))
        for cmd in recipe:
            out.write('\t{}\n'.format(cmd))

    def write(self, out):
        for name, value in self._global_variables.iteritems():
            self._write_variable(out, name, value)
        if self._global_variables:
            out.write('\n')

        for name, value in self._target_variables.iteritems():
            self._write_variable(out, name[1], value, target=name[0])
        if self._target_variables:
            out.write('\n')

        for r in self._rules:
            self._write_rule(out, *r)
            out.write('\n')

        for i in self._includes:
            out.write('{opt}include {name}\n'.format(
                name=i.name, opt='-' if i.optional else ''
            ))


def write(path, edges):
    writer = MakeWriter()
    for e in edges:
        __rule_handlers__[type(e).__name__](writer, e)
    with open(os.path.join(path, 'Makefile'), 'w') as out:
        writer.write(out)

def cmd_var(writer, lang):
    cmd, varname = cc.command_name(lang)
    var = MakeVariable(varname)
    if not writer.has_variable(var):
        writer.variable(var, cmd)
    return var

__seen_compile_rules__ = set() # TODO: put this somewhere else (on the writer?)

@rule_handler('Compile')
def emit_object_file(writer, rule):
    base, ext = os.path.splitext(target_name(rule.file))
    cmd = cmd_var(writer, rule.file.lang)
    cflags = MakeVariable('{}flags'.format(cmd))
    recipe = [
        cc.compile_command(
            cmd=cmd.use(), input='$<', output='$@',
            dep='$*.d', prevars=cflags.use()
        ),
        "@sed -e 's/.*://' -e 's/\\$$//' < $*.d | fmt -1 | \\",
        "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
    ]

    if ext2lang[ext] == rule.file.lang:
        if ext not in __seen_compile_rules__:
            __seen_compile_rules__.add(ext)
            writer.rule(
                target=target_name(ObjectFile('%')),
                deps=['%' + ext], recipe=recipe
            )
    else:
        writer.rule(target=target_name(rule), deps=[target_name(rule.file)],
                    recipe=recipe)

    cflags_value = []
    if rule.target.in_library:
        cflags_value.append(cc.library_flag())
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        writer.variable(cflags.use(), ' '.join(cflags_value),
                        target_name(rule.target))
    writer.include(base + '.d', True)

@rule_handler('Link')
def emit_link(writer, rule):
    if type(rule.target).__name__ == 'Library':
        mode = 'library'
    else:
        mode = 'executable'

    variables = {}
    lib_deps = [i for i in rule.libs if not i.external]

    if len(rule.deps) == 0 and len(lib_deps) == 0:
        inputs = ['$^']
        deps = [target_name(i) for i in rule.files]
    else:
        if len(rule.files) > 1:
            var_name = MakeVariable('OBJS')
            if not writer.has_variable(var_name, target='%'):
                writer.variable(var_name, '', target='%')
            variables[var_name] = ' '.join(
                (target_name(i) for i in rule.files)
            )
            inputs = [var_name.use()]
        else:
            inputs = [target_name(rule.files[0])]

        deps = chain(
            inputs, (target_name(i) for i in chain(rule.deps, lib_deps))
        )

    cmd = cmd_var(writer, (i.lang for i in rule.files))
    writer.rule(
        target=target_name(rule.target), deps=deps,
        recipe=[cc.link_command(
            cmd=cmd.use(), mode=mode, input=inputs,
            libs=rule.libs, output='$@', prevars=rule.compile_options,
            postvars=rule.link_options
        )], variables=variables
    )

@rule_handler('Alias')
def emit_alias(writer, rule):
    writer.rule(
        target=target_name(rule.target),
        deps=(target_name(i) for i in rule.deps),
        recipe=[],
        phony=True
    )

@rule_handler('Command')
def emit_command(writer, rule):
    writer.rule(
        target=target_name(rule.target),
        deps=(target_name(i) for i in rule.deps),
        recipe=rule.cmd,
        phony=True
    )
