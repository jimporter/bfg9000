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
        self.name = re.sub('r[\w:#=]', '_', name).upper()

    def use(self):
        return '$({})'.format(self.name)

    def __str__(self):
        return self.use()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __ne__(self, rhs):
        return self.name != rhs.name

class MakeWriter(object):
    def __init__(self):
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict({'%': OrderedDict()})
        self._defines = OrderedDict()
        self._includes = []
        self._rules = []

    def variable(self, name, value, flavor='simple', target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if self.has_variable(name, target=target):
            raise RuntimeError('variable "{}" already exists'.format(name))

        if flavor == 'define':
            self._defines[name] = value
        else:
            if target:
                if not target in self._target_variables:
                    self._target_variables[target] = OrderedDict()
                self._target_variables[target][name] = (value, flavor)
            else:
                self._global_variables[name] = (value, flavor)
        return name

    def has_variable(self, name, target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if target:
            return (target in self._target_variables and
                    name in self._target_variables[target])
        else:
            return (name in self._global_variables or
                    name in self._defines)

    def include(self, name, optional=False):
        self._includes.append(MakeInclude(name, optional))

    def rule(self, target, deps, recipe, variables=None, phony=False):
        real_variables = {}
        if variables:
            for k, v in variables.iteritems():
                if not isinstance(k, MakeVariable):
                    k = MakeVariable(k)
                real_variables[k] = v

        self._rules.append(MakeRule(target, deps, recipe, real_variables,
                                    phony))

    def _write_variable(self, out, name, value, flavor, target=None):
        operator = ':=' if flavor == 'simple' else '='
        if target:
            out.write('{}: '.format(target))
        out.write('{name} {op} {value}\n'.format(
            name=name.name, op=operator, value=value
        ))

    def _write_define(self, out, name, value):
        out.write('define {name}\n'.format(name=name.name))
        for i in value:
            out.write(i + '\n')
        out.write('endef\n\n')

    def _write_rule(self, out, target, deps, recipe, variables, phony):
        if variables:
            for name, value in variables.iteritems():
                self._write_variable(out, name, value, 'simple', target=target)
        if phony:
            out.write('.PHONY: {}\n'.format(target))
        out.write('{target}:{deps}'.format(
            target=target,
            deps=''.join(' ' + i for i in deps)
        ))

        if isinstance(recipe, MakeVariable):
            out.write(' ; {}'.format(recipe.use()))
        else:
            for cmd in recipe:
                out.write('\n\t{}'.format(cmd))
        out.write('\n\n')

    def write(self, out):
        for name, value in self._global_variables.iteritems():
            self._write_variable(out, name, value[0], value[1])
        if self._global_variables:
            out.write('\n')

        newline = False
        for target, each in self._target_variables.iteritems():
            for name, value in each.iteritems():
                newline = True
                self._write_variable(out, name, value[0], value[1], target)
        if newline:
            out.write('\n')

        for name, value in self._defines.iteritems():
            self._write_define(out, name, value)

        for r in self._rules:
            self._write_rule(out, *r)

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

@rule_handler('Compile')
def emit_object_file(writer, rule):
    base, ext = os.path.splitext(target_name(rule.file))
    cmd = cmd_var(writer, rule.file.lang)
    cflags = MakeVariable('{}FLAGS'.format(cmd.name))
    recipename = MakeVariable('RULE_{}'.format(cmd.name))

    if not writer.has_variable(cflags, target='%'):
        writer.variable(cflags, '', target='%')

    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            cc.compile_command(
                cmd=cmd, input='$<', output='$@',
                dep='$*.d', prevars=cflags
            ),
            "@sed -e 's/.*://' -e 's/\\$$//' < $*.d | fmt -1 | \\",
            "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
        ], flavor='define')

    cflags_value = []
    if rule.target.in_library:
        cflags_value.append(cc.library_flag())
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        writer.variable(cflags.use(), ' '.join(cflags_value),
                        target=target_name(rule.target))

    writer.rule(target=target_name(rule.target), deps=[target_name(rule.file)],
                recipe=recipename)

    writer.include(base + '.d', True)

@rule_handler('Link')
def emit_link(writer, rule):
    cmd = cmd_var(writer, (i.lang for i in rule.files))

    if type(rule.target).__name__ == 'Library':
        recipename = MakeVariable('RULE_{}_LINKLIB'.format(cmd.name))
        mode = 'library'
    else:
        recipename = MakeVariable('RULE_{}_LINK'.format(cmd.name))
        mode = 'executable'

    cflags = MakeVariable('{}FLAGS'.format(cmd.name))
    if not writer.has_variable(cflags, target='%'):
        writer.variable(cflags, '', target='%')

    ldflags = MakeVariable('LDFLAGS')
    if not writer.has_variable(ldflags, target='%'):
        writer.variable(ldflags, '', target='%')

    objs_var = MakeVariable('OBJS')
    if not writer.has_variable(objs_var, target='%'):
        writer.variable(objs_var, '', target='%')

    libs_var = MakeVariable('LIBS')
    if not writer.has_variable(libs_var, target='%'):
        writer.variable(libs_var, '', target='%')

    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            cc.link_command(
                cmd=cmd, mode=mode, input=objs_var, output='$@',
                prevars=cflags, postvars=[libs_var, ldflags]
            )
        ], flavor='define')

    lib_deps = [i for i in rule.libs if not i.external]
    deps = chain(
        [objs_var.use()], (target_name(i) for i in chain(rule.deps, lib_deps))
    )

    variables = {}
    variables[objs_var] = ' '.join(target_name(i) for i in rule.files)
    if rule.libs:
        variables[libs_var] = cc.link_libs(rule.libs)
    if rule.compile_options:
        variables[cflags] = rule.compile_options
    if rule.link_options:
        variables[ldflags] = rule.link_options

    writer.rule(
        target=target_name(rule.target), deps=deps,
        recipe=recipename, variables=variables
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
