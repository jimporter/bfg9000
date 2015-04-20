import os
import re
from collections import OrderedDict, namedtuple
from itertools import chain

from languages import ext2lang

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['target', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

class MakeVariable(object):
    def __init__(self, name):
        self.name = re.sub(r'[\s:#=]', '_', name)

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

srcdir_var = MakeVariable('srcdir')
def target_path(env, target):
    name = env.target_name(target)
    return os.path.join(str(srcdir_var), name) if target.is_source else name

def write(env, build_inputs):
    writer = MakeWriter()
    writer.variable(srcdir_var, env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer, env)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, writer, env)

    with open(os.path.join(env.builddir, 'Makefile'), 'w') as out:
        writer.write(out)

def cmd_var(compiler, writer):
    var = MakeVariable(compiler.command_var.upper())
    if not writer.has_variable(var):
        writer.variable(var, compiler.command_name)
    return var

def all_rule(default_targets, writer, env):
    writer.rule(
        target='all',
        deps=(target_path(env, i) for i in default_targets)
    )

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, writer, env):
    if not install_targets:
        return
    prefix = writer.variable('prefix', env.install_prefix)

    def install_cmd(kind):
        install = MakeVariable('INSTALL')
        if not writer.has_variable(install):
            writer.variable(install, 'install')

        if kind == 'program':
            install_program = MakeVariable('INSTALL_PROGRAM')
            if not writer.has_variable(install_program):
                writer.variable(install_program, install)
            return install_program
        else:
            install_data = MakeVariable('INSTALL_DATA')
            if not writer.has_variable(install_data):
                writer.variable(install_data, '{} -m 644'.format(install))
            return install_data

    recipe = [
        '{install} -D {source} {dest}'.format(
            install=install_cmd(i.install_kind),
            source=target_path(env, i),
            dest=os.path.join(str(prefix), i.install_dir,
                              os.path.basename(target_path(env, i)))
        ) for i in install_targets.files
    ] + [
        'mkdir -p {dest} && cp -r {source} {dest}'.format(
            source=os.path.join(target_path(env, i), '*'),
            dest=os.path.join(str(prefix), i.install_dir)
        ) for i in install_targets.directories
    ]

    writer.rule(target='install', deps=['all'], recipe=recipe, phony=True)

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
    compiler = env.compiler(rule.file.lang)
    recipename = MakeVariable('RULE_{}'.format(compiler.name.upper()))

    cflags = MakeVariable('{}FLAGS'.format(compiler.command_var.upper()))
    if not writer.has_variable(cflags, target='%'):
        writer.variable(cflags, '', target='%')

    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            compiler.command(
                cmd=cmd_var(compiler, writer), input='$<', output='$@',
                dep='$*.d', pre_args=cflags
            ),
            "@sed -e 's/.*://' -e 's/\\\\$$//' < $*.d | fmt -1 | \\",
            "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
        ], flavor='define')

    variables = {}
    cflags_value = []
    if rule.target.in_shared_library:
        cflags_value.extend(compiler.library_args)
    if rule.include:
        cflags_value.extend(compiler.include_dirs(
            target_path(env, i) for i in rule.include
        ))
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(target=env.target_name(rule.target),
                deps=[target_path(env, rule.file)], order_only=order_only,
                recipe=recipename, variables=variables)
    directory_rule(directory, writer)

    base = os.path.splitext(env.target_name(rule.file))[0]
    writer.include(base + '.d', True)

def link_mode(target):
    return {
        'Executable'   : 'executable',
        'SharedLibrary': 'shared_library',
        'StaticLibrary': 'static_library',
    }[type(target).__name__]

@rule_handler('Link')
def emit_link(rule, writer, env):
    linker = env.linker((i.lang for i in rule.files), link_mode(rule.target))
    recipename = MakeVariable('RULE_{}'.format(linker.name.upper()))

    cflags = MakeVariable('{}FLAGS'.format(linker.command_var.upper()))
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
            linker.command(
                cmd=cmd_var(linker, writer), input='$1', output='$@',
                pre_args=cflags, post_args=[libs_var, ldflags]
            )
        ], flavor='define')

    lib_deps = (i for i in rule.libs if not i.is_source)
    deps = (target_path(env, i) for i in chain(rule.files, rule.deps, lib_deps))

    cflags_value = []
    if linker.always_args:
        cflags_value.extend(linker.always_args)
    if rule.compile_options:
        cflags_value.append(rule.compile_options)

    variables = {}
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)
    if rule.libs:
        variables[libs_var] = ' '.join(linker.link_libs(rule.libs))
    if rule.link_options:
        variables[ldflags] = rule.link_options

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(
        target=env.target_name(rule.target), deps=deps, order_only=order_only,
        recipe=MakeCall(recipename, *[target_path(env, i) for i in rule.files]),
        variables=variables
    )
    directory_rule(directory, writer)

@rule_handler('Alias')
def emit_alias(rule, writer, env):
    writer.rule(
        target=env.target_name(rule.target),
        deps=(target_path(env, i) for i in rule.deps),
        recipe=[],
        phony=True
    )

@rule_handler('Command')
def emit_command(rule, writer, env):
    writer.rule(
        target=env.target_name(rule.target),
        deps=(target_path(env, i) for i in rule.deps),
        recipe=rule.cmd,
        phony=True
    )
