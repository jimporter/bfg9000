import os
import re
import sys
from collections import OrderedDict, namedtuple
from itertools import chain

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
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

srcdir_var = NinjaVariable('srcdir')
def target_path(env, target):
    name = env.target_name(target)
    return os.path.join(str(srcdir_var), name) if target.is_source else name

def write(env, build_inputs):
    writer = NinjaWriter()
    writer.variable(srcdir_var, env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer, env)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, writer, env)

    with open(os.path.join(env.builddir, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(compiler, writer):
    var = NinjaVariable(compiler.command_var)
    if not writer.has_variable(var):
        writer.variable(var, compiler.command_name)
    return var

def all_rule(default_targets, writer, env):
    writer.default(['all'])
    writer.build(
        output='all', rule='phony',
        inputs=(target_path(env, i) for i in default_targets)
    )

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, writer, env):
    if not install_targets:
        return
    prefix = writer.variable('prefix', env.install_prefix)

    def install_cmd(kind):
        install = NinjaVariable('install')
        if not writer.has_variable(install):
            writer.variable(install, 'install')

        if kind == 'program':
            install_program = NinjaVariable('install_program')
            if not writer.has_variable(install_program):
                writer.variable(install_program, install)
            return install_program
        else:
            install_data = NinjaVariable('install_data')
            if not writer.has_variable(install_data):
                writer.variable(install_data, '{} -m 644'.format(install))
            return install_data

    if not writer.has_rule('command'):
        writer.rule(name='command', command='$cmd')

    commands = [
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

    writer.build(
        output='install', rule='command', implicit=['all'],
        variables={'cmd': ' && '.join(commands)}
    )

@rule_handler('Compile')
def emit_object_file(rule, writer, env):
    compiler = env.compiler(rule.file.lang)
    cflags = NinjaVariable('{}flags'.format(compiler.command_var))

    if not writer.has_rule(compiler.name):
        writer.rule(name=compiler.name, command=compiler.command(
            cmd=cmd_var(compiler, writer), input='$in', output='$out',
            dep='$out.d', pre_args=cflags
        ), depfile='$out.d')

    variables = {}
    cflags_value = []
    if rule.target.in_shared_library:
        cflags_value.extend(compiler.library_args)
    if rule.include:
        cflags_value.extend(chain.from_iterable(
            compiler.include_dir(target_path(env, i)) for i in rule.include
        ))
    if rule.options:
        cflags_value.append(rule.options)
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)

    writer.build(output=env.target_name(rule.target), rule=compiler.name,
                 inputs=[target_path(env, rule.file)],
                 variables=variables)

def link_mode(target):
    return {
        'Executable'   : 'executable',
        'SharedLibrary': 'shared_library',
        'StaticLibrary': 'static_library',
    }[type(target).__name__]

@rule_handler('Link')
def emit_link(rule, writer, env):
    linker = env.linker((i.lang for i in rule.files), link_mode(rule.target))
    cflags = NinjaVariable('{}flags'.format(linker.command_var))
    libs_var = NinjaVariable('libs')
    ldflags = NinjaVariable('ldflags')

    if not writer.has_rule(linker.name):
        writer.rule(name=linker.name, command=linker.command(
            cmd=cmd_var(linker, writer), input='$in', output='$out',
            pre_args=cflags, post_args=[libs_var, ldflags]
        ))

    cflags_value = []
    if linker.always_args:
        cflags_value.extend(linker.always_args)
    if rule.compile_options:
        cflags_value.append(rule.compile_options)

    variables = {}
    if cflags_value:
        variables[cflags] = ' '.join(cflags_value)
    if rule.libs:
        variables[libs_var] = ' '.join(chain.from_iterable(
            linker.link_lib(os.path.basename(i.name)) for i in rule.libs
        ))
    if rule.link_options:
        variables[ldflags] = rule.link_options

    writer.build(
        output=env.target_name(rule.target), rule=linker.name,
        inputs=(target_path(env, i) for i in rule.files),
        implicit=(target_path(env, i) for i in rule.libs if not i.is_source),
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, writer, env):
    writer.build(
        output=env.target_name(rule.target), rule='phony',
        inputs=[target_path(env, i) for i in rule.deps]
    )

@rule_handler('Command')
def emit_command(rule, writer, env):
    if not writer.has_rule('command'):
        writer.rule(name='command', command='$cmd')
    writer.build(
        output=env.target_name(rule.target), rule='command',
        inputs=(target_path(env, i) for i in rule.deps),
        variables={'cmd': ' && '.join(rule.cmd)}
    )
