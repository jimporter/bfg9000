import os
import re
import sys
from cStringIO import StringIO
from collections import namedtuple, OrderedDict
from itertools import chain

import path
import safe_str
import shell
import utils

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator

NinjaRule = namedtuple('NinjaRule', ['command', 'depfile', 'deps', 'generator'])
NinjaBuild = namedtuple('NinjaBuild', ['outputs', 'rule', 'inputs', 'implicit',
                                       'order_only', 'variables'])

class NinjaVariable(object):
    def __init__(self, name):
        self.name = re.sub('\W', '_', name)

    def use(self):
        return safe_str.escaped_str('${}'.format(self.name))

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, rhs):
        return cmp(self.name, rhs.name)

    def __add__(self, rhs):
        return self.use() + rhs

    def __radd__(self, lhs):
        return lhs + self.use()

var = NinjaVariable

_path_vars = {
    'srcdir': NinjaVariable('srcdir'),
    'prefix': NinjaVariable('prefix'),
}
class NinjaWriter(object):
    def __init__(self):
        # TODO: Sort variables in some useful order
        self._variables = OrderedDict()
        self._rules = OrderedDict()
        self._builds = []
        self._build_outputs = set()
        self._defaults = []

    def variable(self, name, value, syntax='variable'):
        if not isinstance(name, NinjaVariable):
            name = NinjaVariable(name)
        if self.has_variable(name):
            raise ValueError('variable "{}" already exists'.format(name))
        self._variables[name] = (value, syntax)
        return name

    def has_variable(self, name):
        if not isinstance(name, NinjaVariable):
            name = NinjaVariable(name)
        return name in self._variables

    def rule(self, name, command, depfile=None, deps=None, generator=False):
        if re.search('\W', name):
            raise ValueError('rule name contains invalid characters')
        if self.has_rule(name):
            raise ValueError('rule "{}" already exists'.format(name))
        self._rules[name] = NinjaRule(command, depfile, deps, generator)

    def has_rule(self, name):
        return name in self._rules

    def build(self, output, rule, inputs=None, implicit=None, order_only=None,
              variables=None):
        if rule != 'phony' and not self.has_rule(rule):
            raise ValueError('unknown rule "{}"'.format(rule))

        real_variables = {}
        if variables:
            for k, v in variables.iteritems():
                if not isinstance(k, NinjaVariable):
                    k = NinjaVariable(k)
                real_variables[k] = v

        outputs = utils.listify(output)
        for i in outputs:
            if self.has_build(i):
                raise ValueError('build for "{}" already exists'.format(i))
            self._build_outputs.add(i)
        self._builds.append(NinjaBuild(
            outputs, rule, utils.listify(inputs), utils.listify(implicit),
            utils.listify(order_only), real_variables
        ))

    def has_build(self, name):
        return name in self._build_outputs

    def default(self, paths):
        self._defaults.extend(paths)

    @classmethod
    def escape_str(cls, string, syntax):
        if syntax == 'output':
            return re.sub(r'([:$\n ])', r'$\1', string)
        elif syntax == 'input' or syntax == 'variable':
            return re.sub(r'([$\n ])', r'$\1', string)
        elif syntax == 'shell_line':
            return string.replace('$', '$$')
        elif syntax == 'shell_word':
            return shell.quote(string).replace('$', '$$')
        else:
            raise ValueError('unknown syntax "{}"'.format(syntax))

    @classmethod
    def _write_literal(cls, out, string):
        out.write(string)

    @classmethod
    def _write(cls, out, thing, syntax):
        thing = safe_str.safe_str(thing)

        if isinstance(thing, basestring):
            cls._write_literal(out, cls.escape_str(thing, syntax))
        elif isinstance(thing, safe_str.escaped_str):
            cls._write_literal(out, thing.string)
        elif isinstance(thing, path.real_path):
            if thing.base != 'builddir':
                cls._write(out, _path_vars[thing.base], syntax)
                cls._write_literal(out, os.sep)
            cls._write(out, thing.path, syntax)
        elif isinstance(thing, safe_str.jbos):
            for j in thing.bits:
                cls._write(out, j, syntax)
        else:
            raise TypeError(type(thing))

    @classmethod
    def _write_each(cls, out, things, syntax, delim=' ', prefix=None,
                    suffix=None):
        for tween, i in utils.tween(things, delim, prefix, suffix):
            cls._write_literal(out, i) if tween else cls._write(out, i, syntax)

    def _write_variable(self, out, name, value, indent=0, syntax='variable'):
        self._write_literal(out, ('  ' * indent) + name.name + ' = ')
        self._write_each(out, utils.iterate(value), syntax)
        self._write_literal(out, '\n')

    def _write_rule(self, out, name, rule):
        self._write_literal(out, 'rule ' + name + '\n')

        self._write_variable(out, var('command'), rule.command, 1, 'shell_word')
        if rule.depfile:
            self._write_variable(out, var('depfile'), rule.depfile, 1)
        if rule.deps:
            self._write_variable(out, var('deps'), rule.deps, 1)
        if rule.generator:
            self._write_variable(out, var('generator'), '1', 1)

    def _write_build(self, out, build):
        self._write_literal(out, 'build ')
        self._write_each(out, build.outputs, syntax='output')
        self._write_literal(out, ': ' + build.rule)

        self._write_each(out, build.inputs, syntax='input', prefix=' ')
        self._write_each(out, build.implicit, syntax='input', prefix=' | ')
        self._write_each(out, build.order_only, syntax='input', prefix=' || ')
        self._write_literal(out, '\n')

        if build.variables:
            for k, v in build.variables.iteritems():
                self._write_variable(out, k, v, 1, 'shell_word')

    def write(self, out):
        for name, (value, syntax) in self._variables.iteritems():
            self._write_variable(out, name, value, syntax=syntax)
        if self._variables:
            self._write_literal(out, '\n')

        for name, rule in self._rules.iteritems():
            self._write_rule(out, name, rule)
            self._write_literal(out, '\n')

        for build in self._builds:
            self._write_build(out, build)

        if self._defaults:
            self._write_literal(out, '\ndefault ')
            self._write_each(out, self._defaults, syntax='input')
            self._write_literal(out, '\n')

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
        writer.variable(global_flags, value, syntax='shell_word')

    flags = NinjaVariable('{}'.format(name))
    if not writer.has_variable(flags):
        writer.variable(flags, global_flags, syntax='shell_word')

    return global_flags, flags

def all_rule(default_targets, writer):
    writer.default(['all'])
    writer.build(
        output='all',
        rule='phony',
        inputs=[i.path for i in default_targets]
    )

def chain_commands(commands, delim=' && '):
    out = StringIO()
    for tween, line in utils.tween(commands, delim):
        if tween:
            NinjaWriter._write_literal(out, line)
        else:
            if utils.isiterable(line):
                NinjaWriter._write_each(out, line, 'shell_word')
            else:
                NinjaWriter._write(out, line, 'shell_line')
    return safe_str.escaped_str(out.getvalue())

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, writer, env):
    if not install_targets:
        return

    writer.variable(_path_vars['prefix'], env.install_prefix)

    def install_cmd(kind):
        install = NinjaVariable('install')
        if not writer.has_variable(install):
            writer.variable(install, 'install', syntax='shell_word')

        if kind == 'program':
            install_program = NinjaVariable('install_program')
            if not writer.has_variable(install_program):
                writer.variable(install_program, install)
            return install_program
        else:
            install_data = NinjaVariable('install_data')
            if not writer.has_variable(install_data):
                writer.variable(install_data, [install, '-m', '644'],
                                syntax='shell_word')
            return install_data

    if not writer.has_rule('command'):
        writer.rule(name='command', command=var('cmd'))

    def install_line(file):
        src = file.path.local_path()
        dst = file.path.install_path()
        return [ install_cmd(file.install_kind), '-D', src, dst ]

    def mkdir_line(dir):
        src = dir.path.append('*').local_path()
        dst = dir.path.parent().install_path()
        return 'mkdir -p ' + dst + ' && cp -r ' + src + ' ' + dst

    commands = chain((install_line(i) for i in install_targets.files),
                     (mkdir_line(i) for i in install_targets.directories))
    writer.build(
        output='install',
        rule='command',
        implicit=['all'],
        variables={'cmd': chain_commands(commands)}
    )

def regenerate_rule(writer, env):
    writer.rule(
        name='regenerate',
        command=[env.bfgpath, '--regenerate', '.'],
        generator=True
    )
    writer.build(
        output=path.Path('build.ninja', path.Path.builddir, path.Path.basedir),
        rule='regenerate',
        implicit=[path.Path('build.bfg', path.Path.srcdir, path.Path.basedir)]
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
        compiler.include_dir(i) for i in rule.include
    ))
    cflags_value.extend(rule.options)
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    if not writer.has_rule(compiler.name):
        command_kwargs = {}
        depfile = None
        deps = None
        if compiler.deps_flavor == 'gcc':
            deps = 'gcc'
            command_kwargs['deps'] = depfile = var('out') + '.d'
        elif compiler.deps_flavor == 'msvc':
            deps = 'msvc'
            command_kwargs['deps'] = True

        writer.rule(name=compiler.name, command=compiler.command(
            cmd=cmd_var(compiler, writer), input=var('in'), output=var('out'),
            args=cflags, **command_kwargs
        ), depfile=depfile, deps=deps)

    writer.build(
        output=rule.target.path,
        rule=compiler.name,
        inputs=[rule.file.path],
        implicit=[i.path for i in rule.extra_deps],
        variables=variables
    )

@rule_handler('Link')
def emit_link(rule, build_inputs, writer):
    linker = rule.builder
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'flags', linker.global_args, writer
    )

    # TODO: Handle rules with multiple targets (e.g. shared libs on Windows).
    path = rule.target.path
    target_dir = path.parent()

    variables = {}
    command_kwargs = {}
    ldflags_value = list(linker.mode_args)
    lib_deps = [i for i in rule.libs if i.creator]

    # TODO: Create a more flexible way of determining when to use these options?
    if linker.mode != 'static_library':
        ldflags_value.extend(rule.options)
        ldflags_value.extend(linker.lib_dirs(lib_deps))

        target_dirname = target_dir.local_path().path
        ldflags_value.extend(linker.rpath(
            # TODO: Provide a relpath function for Path objects?
            os.path.relpath(i.path.parent().local_path().path, target_dirname)
            for i in lib_deps
        ))

        global_ldlibs, ldlibs = flags_vars(
            linker.link_var + 'libs', linker.global_libs, writer
        )
        command_kwargs['libs'] = ldlibs
        if rule.libs:
            variables[ldlibs] = [global_ldlibs] + list(chain.from_iterable(
                linker.link_lib(i) for i in rule.libs
            ))

    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    if not writer.has_rule(linker.name):
        writer.rule(name=linker.name, command=linker.command(
            cmd=cmd_var(linker, writer), input=var('in'), output=var('out'),
            args=ldflags, **command_kwargs
        ))

    writer.build(
        output=path,
        rule=linker.name,
        inputs=[i.path for i in rule.files],
        implicit=[i.path for i in chain(lib_deps, rule.extra_deps)],
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, build_inputs, writer):
    writer.build(
        output=rule.target.path,
        rule='phony',
        inputs=[i.path for i in rule.extra_deps]
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, writer):
    if not writer.has_rule('command'):
        writer.rule(name='command', command=var('cmd'))

    e = safe_str.escaped_str
    writer.build(
        output=rule.target.path,
        rule='command',
        inputs=[i.path for i in rule.extra_deps],
        variables={'cmd': chain_commands(rule.cmd)}
    )
