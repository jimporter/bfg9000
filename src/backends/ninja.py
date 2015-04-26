import os
import re
import sys
from collections import Iterable, namedtuple, OrderedDict
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
class escaped_str(str):
    @staticmethod
    def escape(value):
        if not isinstance(value, basestring):
            raise TypeError('escape only works on strings')
        if not isinstance(value, escaped_str):
            # TODO: Handle other escape chars
            value = value.replace('$', '$$')
        return value

    def __str__(self):
        return self

    def __add__(self, rhs):
        return escaped_str(str.__add__( self, escaped_str.escape(rhs) ))

    def __radd__(self, lhs):
        return escaped_str(str.__add__( escaped_str.escape(lhs), self ))

def escape_str(value):
    return escaped_str.escape(str(value))

def escape_list(value, delim=' '):
    if isinstance(value, Iterable) and not isinstance(value, basestring):
        return escaped_str(delim.join(escape_str(i) for i in value if i))
    else:
        return escape_str(value)

def path_join(*args):
    return escape_list(args, delim=os.sep)

class NinjaVariable(object):
    def __init__(self, name):
        self.name = re.sub('/', '_', name)

    def use(self):
        return escaped_str('${}'.format(self.name))

    def __str__(self):
        return self.use()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __ne__(self, rhs):
        return self.name != rhs.name

    def __add__(self, rhs):
        return str(self) + rhs

    def __radd__(self, lhs):
        return lhs + str(self)

var = NinjaVariable

class NinjaWriter(object):
    def __init__(self):
        # TODO: Sort variables in some useful order
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
            indent='  ' * indent, name=name.name, value=escape_list(value)
        ))

    def _write_rule(self, out, name, rule):
        out.write('rule {}\n'.format(escape_str(name)))
        self._write_variable(out, var('command'), rule.command, 1)
        if rule.depfile:
            self._write_variable(out, var('depfile'), rule.depfile, 1)

    def _write_build(self, out, name, build):
        out.write('build {output}: {rule}'.format(
            output=escape_str(name),
            rule=escape_str(build.rule)
        ))

        for i in build.inputs or []:
            out.write(' ' + escape_str(i))

        first = True
        for i in build.implicit or []:
            if first:
                first = False
                out.write(' |')
            out.write(' ' + escape_str(i))

        first = True
        for i in build.order_only or []:
            if first:
                first = False
                out.write(' ||')
            out.write(' ' + escape_str(i))

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
            out.write('\ndefault {}\n'.format(' '.join(
                escape_str(i) for i in self._defaults
            )))

srcdir_var = NinjaVariable('srcdir')
def target_path(env, target):
    name = target.filename(env)
    return os.path.join(str(srcdir_var), name) if target.is_source else name

def write(env, build_inputs):
    writer = NinjaWriter()
    writer.variable(srcdir_var, env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer, env)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, writer, env)

    with open(os.path.join(env.builddir, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(compiler, writer):
    var = NinjaVariable(compiler.command_var)
    if not writer.has_variable(var):
        writer.variable(var, compiler.command_name)
    return var

def flags_vars(lang, value, writer):
    if value is None:
        return None, None

    global_flags = NinjaVariable('global_{}flags'.format(lang))
    if not writer.has_variable(global_flags):
        writer.variable(global_flags, ' '.join(value))
    flags = NinjaVariable('{}flags'.format(lang))
    if not writer.has_variable(flags):
        writer.variable(flags, str(global_flags))

    return global_flags, flags

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
                writer.variable(install_data, [install, '-m', '644'])
            return install_data

    if not writer.has_rule('command'):
        writer.rule(name='command', command=var('cmd'))

    def install_line(file):
        src = target_path(env, file)
        dst = path_join(
            prefix, file.install_dir, os.path.basename(file.filename(env))
        )
        return [ install_cmd(file.install_kind), '-D', src, dst ]

    def mkdir_line(dir):
        src = path_join(target_path(env, dir), '*')
        dst = path_join(prefix, dir.install_dir)
        return ['mkdir', '-p', dst, '&&', 'cp', '-r', src, dst]

    commands = ([install_line(i) for i in install_targets.files] +
                [mkdir_line(i) for i in install_targets.directories])
    writer.build(
        output='install', rule='command', implicit=['all'],
        # TODO: Improve how variables are defined here
        variables={'cmd': escaped_str(
            ' && '.join(escape_list(i) for i in commands)
        )}
    )

@rule_handler('Compile')
def emit_object_file(rule, build_inputs, writer, env):
    lang = rule.file.lang
    compiler = env.compiler(lang)

    global_cflags, cflags = flags_vars(
        compiler.command_var,
        compiler.global_args + build_inputs.global_options.get(lang, []),
        writer
    )
    if not writer.has_rule(compiler.name):
        writer.rule(name=compiler.name, command=compiler.command(
            cmd=cmd_var(compiler, writer), input=var('in'), output=var('out'),
            dep=var('out') + '.d', args=cflags
        ), depfile=var('out') + '.d')

    variables = {}

    cflags_value = []
    if rule.target.in_shared_library:
        cflags_value.extend(compiler.library_args)
    cflags_value.extend(chain.from_iterable(
        compiler.include_dir(target_path(env, i)) for i in rule.include
    ))
    cflags_value.extend(rule.options)
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    writer.build(output=rule.target.filename(env), rule=compiler.name,
                 inputs=[target_path(env, rule.file)],
                 variables=variables)

# TODO: Remove this
def link_mode(target):
    return {
        'Executable'   : 'executable',
        'SharedLibrary': 'shared_library',
        'StaticLibrary': 'static_library',
    }[type(target).__name__]

@rule_handler('Link')
def emit_link(rule, build_inputs, writer, env):
    linker = env.linker(rule.target.langs, link_mode(rule.target))

    global_ldflags, ldflags = flags_vars(
        linker.link_var, linker.global_args, writer
    )
    ldlibs = NinjaVariable('{}libs'.format(linker.link_var))
    if not writer.has_rule(linker.name):
        writer.rule(name=linker.name, command=linker.command(
            cmd=cmd_var(linker, writer), input=var('in'), output=var('out'),
            libs=ldlibs, args=ldflags
        ))

    variables = {}

    ldflags_value = []
    ldflags_value.extend(linker.mode_args)
    ldflags_value.extend(rule.options)

    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    if rule.libs:
        variables[ldlibs] = list(chain.from_iterable(
            linker.link_lib(i.lib_name) for i in rule.libs
        ))

    writer.build(
        output=rule.target.filename(env), rule=linker.name,
        inputs=(target_path(env, i) for i in rule.files),
        implicit=(target_path(env, i) for i in rule.libs if not i.is_source),
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, build_inputs, writer, env):
    writer.build(
        output=rule.target.filename(env), rule='phony',
        inputs=[target_path(env, i) for i in rule.deps]
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, writer, env):
    if not writer.has_rule('command'):
        writer.rule(name='command', command=var('cmd'))
    writer.build(
        output=rule.target.filename(env), rule='command',
        inputs=(target_path(env, i) for i in rule.deps),
        variables={'cmd': ' && '.join(rule.cmd)}
    )
