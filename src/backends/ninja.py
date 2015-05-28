import os
import re
import sys
from collections import Iterable, namedtuple, OrderedDict
from itertools import chain

import utils
from path import Path

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator

NinjaRule = namedtuple('NinjaRule', ['command', 'depfile', 'generator'])
NinjaBuild = namedtuple('NinjaBuild', ['output', 'rule', 'inputs', 'implicit',
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
        self._builds = []
        self._build_outputs = set()
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

    def rule(self, name, command, depfile=None, generator=False):
        if self.has_rule(name):
            raise RuntimeError('rule "{}" already exists'.format(name))
        self._rules[name] = NinjaRule(command, depfile, generator)

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

        for i in utils.iterate(output):
            if self.has_build(i):
                raise RuntimeError('build for "{}" already exists'.format(i))
            self._build_outputs.add(i)
        self._builds.append(NinjaBuild(output, rule, inputs, implicit,
                                       order_only, real_variables))

    def has_build(self, name):
        return name in self._build_outputs

    def default(self, paths):
        self._defaults.extend(paths)

    def _write_variable(self, out, name, value, indent=0):
        out.write('{indent}{name} = {value}\n'.format(
            indent='  ' * indent, name=name.name, value=escape_list(value)
        ))

    def _write_rule(self, out, name, rule):
        out.write('rule {}\n'.format(escape_list(name)))
        self._write_variable(out, var('command'), rule.command, 1)
        if rule.depfile:
            self._write_variable(out, var('depfile'), rule.depfile, 1)
        if rule.generator:
            self._write_variable(out, var('generator'), 1, 1)

    def _write_build(self, out, build):
        out.write('build {output}: {rule}'.format(
            output=escape_list(build.output),
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

        for build in self._builds:
            self._write_build(out, build)

        if self._defaults:
            out.write('\ndefault {}\n'.format(' '.join(
                escape_str(i) for i in self._defaults
            )))

_path_vars = {
    'srcdir': NinjaVariable('srcdir'),
    'prefix': NinjaVariable('prefix'),
}
def path_str(path, form='local_path'):
    source, pathname = getattr(path, form)()
    if source:
        return escape_list([_path_vars[source], pathname], os.sep)
    else:
        return escape_str(pathname)

def write(env, build_inputs):
    writer = NinjaWriter()
    writer.variable(_path_vars['srcdir'], env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, writer)
    regenerate_rule(writer, env)

    with open(os.path.join(env.builddir, 'build.ninja'), 'w') as out:
        writer.write(out)

def cmd_var(compiler, writer):
    var = NinjaVariable(compiler.command_var)
    if not writer.has_variable(var):
        writer.variable(var, compiler.command_name)
    return var

def flags_vars(name, value, writer):
    global_flags = NinjaVariable('global_{}'.format(name))
    if not writer.has_variable(global_flags):
        writer.variable(global_flags, ' '.join(value))

    flags = NinjaVariable('{}'.format(name))
    if not writer.has_variable(flags):
        writer.variable(flags, str(global_flags))

    return global_flags, flags

def all_rule(default_targets, writer):
    writer.default(['all'])
    writer.build(
        output='all', rule='phony',
        inputs=(path_str(i.path) for i in default_targets)
    )

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, writer, env):
    if not install_targets:
        return

    writer.variable(_path_vars['prefix'], env.install_prefix)

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
        src = path_str(file.path)
        dst = path_str(file.path, 'install_path')
        return [ install_cmd(file.install_kind), '-D', src, dst ]

    def mkdir_line(dir):
        src = path_str(dir.path.append('*'))
        dst = path_str(dir.path.parent(), 'install_path')
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

def regenerate_rule(writer, env):
    writer.rule(
        name='regenerate',
        command=[env.bfgpath, '--regenerate', '.'],
        generator=True
    )
    writer.build(
        output='build.ninja', rule='regenerate',
        implicit=[path_str(Path('build.bfg', Path.srcdir, Path.basedir))]
    )

@rule_handler('Compile')
def emit_object_file(rule, build_inputs, writer):
    compiler = rule.builder
    global_cflags, cflags = flags_vars(
        compiler.command_var + 'flags',
        compiler.global_args +
          build_inputs.global_options.get(rule.file.lang, []),
        writer
    )

    variables = {}

    cflags_value = []
    if rule.in_shared_library:
        cflags_value.extend(compiler.library_args)
    cflags_value.extend(chain.from_iterable(
        compiler.include_dir(path_str(i.path)) for i in rule.include
    ))
    cflags_value.extend(rule.options)
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    if not writer.has_rule(compiler.name):
        writer.rule(name=compiler.name, command=compiler.command(
            cmd=cmd_var(compiler, writer), input=var('in'), output=var('out'),
            dep=var('out') + '.d', args=cflags
        ), depfile=var('out') + '.d')

    writer.build(output=path_str(rule.target.path), rule=compiler.name,
                 inputs=[path_str(rule.file.path)],
                 implicit=(path_str(i.path) for i in rule.extra_deps),
                 variables=variables)

@rule_handler('Link')
def emit_link(rule, build_inputs, writer):
    linker = rule.builder
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'flags', linker.global_args, writer
    )

    # TODO: Handle rules with multiple targets (e.g. shared libs on Windows).
    path = rule.target.path
    target_dir = path.parent()
    target_dirname = path_str(target_dir)

    variables = {}
    command_kwargs = {}
    ldflags_value = linker.mode_args[:]
    lib_deps = [i for i in rule.libs if i.creator]

    # TODO: Create a more flexible way of determining when to use these options?
    if linker.mode != 'static_library':
        lib_dirs = set(os.path.dirname(path_str(i.path)) for i in lib_deps)
        ldflags_value.extend(rule.options)
        ldflags_value.extend(chain.from_iterable(
            linker.lib_dir(i) for i in lib_dirs
        ))
        ldflags_value.extend(linker.rpath(
            # TODO: Provide a relpath function for Path objects?
            os.path.relpath(i, target_dirname) for i in lib_dirs
        ))

        global_ldlibs, ldlibs = flags_vars(
            linker.link_var + 'LIBS', linker.global_libs, writer
        )
        command_kwargs['libs'] = ldlibs
        if rule.libs:
            variables[ldlibs] = [global_ldlibs] + list(chain.from_iterable(
                linker.link_lib(i.lib_name) for i in rule.libs
            ))

    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    if not writer.has_rule(linker.name):
        writer.rule(name=linker.name, command=linker.command(
            cmd=cmd_var(linker, writer), input=var('in'), output=var('out'),
            args=ldflags, **command_kwargs
        ))

    writer.build(
        output=path_str(path), rule=linker.name,
        inputs=(path_str(i.path) for i in rule.files),
        implicit=(path_str(i.path) for i in chain(lib_deps, rule.extra_deps)),
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, build_inputs, writer):
    writer.build(
        output=path_str(rule.target.path), rule='phony',
        inputs=[path_str(i.path) for i in rule.extra_deps]
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, writer):
    if not writer.has_rule('command'):
        writer.rule(name='command', command=var('cmd'))
    writer.build(
        output=path_str(rule.target.path), rule='command',
        inputs=(path_str(i.path) for i in rule.extra_deps),
        variables={'cmd': ' && '.join(rule.cmd)}
    )
