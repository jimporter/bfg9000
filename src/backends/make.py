import os
import re
from collections import OrderedDict, namedtuple
from itertools import chain

import toolchains.cc
from builtin_rules import ObjectFile
from languages import ext2lang

cc = toolchains.cc.CcCompiler() # TODO: make this replaceable

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['target', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

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

class MakeCall(object):
    def __init__(self, name, *args):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        self.name = name
        self.args = args

    def __str__(self):
        return '$(call {})'.format(
            ','.join(chain([self.name.name], self.args))
        )

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

    def rule(self, target, deps=None, order_only=None, recipe=None,
             variables=None, phony=False):
        real_variables = {}
        if variables:
            for k, v in variables.iteritems():
                if not isinstance(k, MakeVariable):
                    k = MakeVariable(k)
                real_variables[k] = v

        self._rules.append(MakeRule(target, deps, order_only, recipe,
                                    real_variables, phony))

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

    def _write_rule(self, out, rule):
        if rule.variables:
            for name, value in rule.variables.iteritems():
                self._write_variable(out, name, value, 'simple',
                                     target=rule.target)

        if rule.phony:
            out.write('.PHONY: {}\n'.format(rule.target))
        out.write('{target}:{deps}'.format(
            target=rule.target,
            deps=''.join(' ' + i for i in rule.deps or [])
        ))

        first = True
        for i in rule.order_only or []:
            if first:
                first = False
                out.write(' |')
            out.write(' ' + i)

        if (isinstance(rule.recipe, MakeVariable) or
            isinstance(rule.recipe, MakeCall)):
            out.write(' ; {}'.format(rule.recipe))
        elif rule.recipe is not None:
            for cmd in rule.recipe:
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
            self._write_rule(out, r)

        for i in self._includes:
            out.write('{opt}include {name}\n'.format(
                name=i.name, opt='-' if i.optional else ''
            ))


def write(env, build_inputs):
    writer = MakeWriter()
    srcdir_var = writer.variable('SRCDIR', env.srcdir)
    env.set_srcdir_var(srcdir_var)

    writer.rule(
        target='all',
        deps=(env.target_path(i) for i in build_inputs.default_targets)
    )
    for e in build_inputs.edges:
        __rule_handlers__[type(e).__name__](e, writer, env)

    with open(os.path.join(env.builddir, 'Makefile'), 'w') as out:
        writer.write(out)

def cmd_var(writer, lang):
    cmd, varname = cc.command_name(lang)
    var = MakeVariable(varname)
    if not writer.has_variable(var):
        writer.variable(var, cmd)
    return var

_seen_dirs = set() # TODO: Put this on the writer
def directory_rule(path, writer):
    if not path or path in _seen_dirs:
        return
    _seen_dirs.add(path)

    recipename = MakeVariable('RULE_MKDIR')
    if not writer.has_variable(recipename):
        writer.variable(recipename, ['mkdir $@'], flavor='define')

    parent = os.path.dirname(path)
    order_only = [parent] if parent else None
    writer.rule(target=path, order_only=order_only, recipe=recipename)
    if parent:
        directory_rule(parent, writer)

@rule_handler('Compile')
def emit_object_file(rule, writer, env):
    base, ext = os.path.splitext(env.target_name(rule.file))
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
            "@sed -e 's/.*://' -e 's/\\\\$$//' < $*.d | fmt -1 | \\",
            "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
        ], flavor='define')

    variables = {}
    cflags_value = []
    if rule.target.in_library:
        cflags_value.append(cc.library_flag())
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(target=env.target_name(rule.target),
                deps=[env.target_path(rule.file)], order_only=order_only,
                recipe=recipename, variables=variables)
    directory_rule(directory, writer)

    writer.include(base + '.d', True)

@rule_handler('Link')
def emit_link(rule, writer, env):
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

    libs_var = MakeVariable('LIBS')
    if not writer.has_variable(libs_var, target='%'):
        writer.variable(libs_var, '', target='%')

    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            cc.link_command(
                cmd=cmd, mode=mode, input='$1', output='$@',
                prevars=cflags, postvars=[libs_var, ldflags]
            )
        ], flavor='define')

    lib_deps = (i for i in rule.libs if not i.is_source)
    deps = (env.target_path(i) for i in chain(rule.files, rule.deps, lib_deps))

    variables = {}
    if rule.libs:
        variables[libs_var] = cc.link_libs(rule.libs)
    if rule.compile_options:
        variables[cflags] = rule.compile_options
    if rule.link_options:
        variables[ldflags] = rule.link_options

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(
        target=env.target_name(rule.target), deps=deps, order_only=order_only,
        recipe=MakeCall(recipename, *[env.target_path(i) for i in rule.files]),
        variables=variables
    )
    directory_rule(directory, writer)

@rule_handler('Alias')
def emit_alias(rule, writer, env):
    writer.rule(
        target=env.target_name(rule.target),
        deps=(env.target_path(i) for i in rule.deps),
        recipe=[],
        phony=True
    )

@rule_handler('Command')
def emit_command(rule, writer, env):
    writer.rule(
        target=env.target_name(rule.target),
        deps=(env.target_path(i) for i in rule.deps),
        recipe=rule.cmd,
        phony=True
    )
