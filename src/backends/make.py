import os
import re
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

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['target', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

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

class MakeVariable(object):
    def __init__(self, name):
        self.name = re.sub(r'[\s:#=]', '_', name)

    def use(self):
        fmt = '${}' if len(self.name) == 1 else '$({})'
        return escaped_str(fmt.format(self.name))

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

var = MakeVariable

class MakeCall(object):
    def __init__(self, name, *args):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        self.name = name
        self.args = args

    def __str__(self):
        return escaped_str('$(call {})'.format(
            ','.join(chain(
                [self.name.name], (escape_list(i) for i in self.args)
            ))
        ))

class MakeWriter(object):
    def __init__(self):
        # TODO: Sort variables in some useful order
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict({'%': OrderedDict()})
        self._defines = OrderedDict()

        self._rules = []
        self._targets = set()
        self._includes = []

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

        for i in utils.iterate(target):
            if self.has_rule(i):
                raise RuntimeError('rule for "{}" already exists'.format(i))
            self._targets.add(i)
        self._rules.append(MakeRule(target, deps, order_only, recipe,
                                    real_variables, phony))

    def has_rule(self, name):
        return name in self._targets

    def _write_variable(self, out, name, value, flavor, target=None):
        operator = ':=' if flavor == 'simple' else '='
        if target:
            out.write('{}: '.format(escape_list(target)))
        out.write('{name} {op} {value}\n'.format(
            name=name.name, op=operator, value=escape_list(value)
        ))

    def _write_define(self, out, name, value):
        out.write('define {name}\n'.format(name=name.name))
        for i in value:
            out.write(escape_list(i) + '\n')
        out.write('endef\n\n')

    def _write_rule(self, out, rule):
        if rule.variables:
            for name, value in rule.variables.iteritems():
                self._write_variable(out, name, value, 'simple',
                                     target=rule.target)

        if rule.phony:
            out.write('.PHONY: {}\n'.format(escape_list(rule.target)))
        out.write('{target}:{deps}'.format(
            target=escape_list(rule.target),
            deps=''.join(' ' + escape_str(i) for i in rule.deps or [])
        ))

        first = True
        for i in rule.order_only or []:
            if first:
                first = False
                out.write(' |')
            out.write(' ' + escape_str(i))

        if (isinstance(rule.recipe, MakeVariable) or
            isinstance(rule.recipe, MakeCall)):
            out.write(' ; {}'.format(escape_str(rule.recipe)))
        elif rule.recipe is not None:
            for cmd in rule.recipe:
                out.write('\n\t{}'.format(escape_list(cmd)))
        out.write('\n\n')

    def write(self, out):
        # Don't let make use built-in suffix rules
        out.write('.SUFFIXES:\n\n')

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
                name=escape_str(i.name), opt='-' if i.optional else ''
            ))

_path_vars = {
    'srcdir': MakeVariable('srcdir'),
    'prefix': MakeVariable('prefix'),
}
def path_str(path, form='local_path'):
    source, pathname = getattr(path, form)()
    if source:
        return escape_list([_path_vars[source], pathname], os.sep)
    else:
        return escape_str(pathname)

def write(env, build_inputs):
    writer = MakeWriter()
    writer.variable(_path_vars['srcdir'], env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, writer)
    regenerate_rule(writer, env)

    with open(os.path.join(env.builddir, 'Makefile'), 'w') as out:
        writer.write(out)

def cmd_var(compiler, writer):
    var = MakeVariable(compiler.command_var.upper())
    if not writer.has_variable(var):
        writer.variable(var, compiler.command_name)
    return var

def flags_vars(name, value, writer):
    name = name.upper()
    global_flags = MakeVariable('GLOBAL_{}'.format(name))
    if not writer.has_variable(global_flags):
        writer.variable(global_flags, value)

    flags = MakeVariable(name)
    if not writer.has_variable(flags, target='%'):
        writer.variable(flags, global_flags, target='%')

    return global_flags, flags

def all_rule(default_targets, writer):
    writer.rule(
        target='all',
        deps=(path_str(i.path) for i in default_targets)
    )

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, writer, env):
    if not install_targets:
        return

    writer.variable(_path_vars['prefix'], env.install_prefix)

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
                writer.variable(install_data, [install, '-m', '644'])
            return install_data

    def install_line(file):
        src = path_str(file.path)
        dst = path_str(file.path, 'install_path')
        return [ install_cmd(file.install_kind), '-D', src, dst ]

    def mkdir_line(dir):
        src = path_str(dir.path.append('*'))
        dst = path_str(dir.path.parent(), 'install_path')
        return ['mkdir', '-p', dst, '&&', 'cp', '-r', src, dst]

    recipe = ([install_line(i) for i in install_targets.files] +
              [mkdir_line(i) for i in install_targets.directories])
    writer.rule(target='install', deps=['all'], recipe=recipe, phony=True)

def regenerate_rule(writer, env):
    writer.rule(
        target='Makefile',
        deps=[path_str(Path('build.bfg', Path.srcdir, Path.basedir))],
        recipe=[[env.bfgpath, '--regenerate', '.']]
    )

def directory_rule(path, writer):
    pathname = path_str(path)
    if not path or writer.has_rule(pathname):
        return

    # XXX: `mkdir -p` isn't safe (or valid!) on all platforms.
    recipe = var('RULE_MKDIR_P')
    if not writer.has_variable(recipe):
        writer.variable(recipe, [['mkdir', '-p', var('@')]], flavor='define')
    writer.rule(target=pathname, recipe=recipe)

@rule_handler('Compile')
def emit_object_file(rule, build_inputs, writer):
    compiler = rule.builder
    recipename = MakeVariable('RULE_{}'.format(compiler.name.upper()))
    global_cflags, cflags = flags_vars(
        compiler.command_var + 'FLAGS',
        compiler.global_args +
          build_inputs.global_options.get(rule.file.lang, []),
        writer
    )

    path = rule.target.path
    target_dir = path.parent()

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

    if not writer.has_variable(recipename):
        depfile = var('@') + '.d'
        writer.variable(recipename, [
            compiler.command(
                cmd=cmd_var(compiler, writer), input=var('<'), output=var('@'),
                dep=depfile, args=cflags
            ),
            # Munge the depfile so that it works a little better...
            r"@sed -e 's/.*://' -e 's/\\$//' < " + depfile + " | fmt -1 | \\",
            "  sed -e 's/^ *//' -e 's/$/:/' >> " + depfile
        ], flavor='define')

    writer.rule(
        target=path_str(path),
        deps=(path_str(i.path) for i in chain([rule.file], rule.extra_deps)),
        order_only=[path_str(target_dir)] if target_dir else None,
        recipe=recipename,
        variables=variables
    )
    directory_rule(target_dir, writer)
    writer.include(path_str(path.addext('.d')), optional=True)

@rule_handler('Link')
def emit_link(rule, build_inputs, writer):
    linker = rule.builder
    recipename = MakeVariable('RULE_{}'.format(linker.name.upper()))
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'FLAGS', linker.global_args, writer
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
        lib_dirs = set(path_str(i.path.parent()) for i in lib_deps)

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

    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            linker.command(
                cmd=cmd_var(linker, writer), input=var('1'), output=var('@'),
                args=ldflags, **command_kwargs
            )
        ], flavor='define')

    writer.rule(
        target=path_str(path),
        deps=(path_str(i.path) for i in chain(rule.files, lib_deps,
                                              rule.extra_deps)),
        order_only=[target_dirname] if target_dir else None,
        recipe=MakeCall(recipename, (path_str(i.path) for i in rule.files)),
        variables=variables
    )
    directory_rule(target_dir, writer)

@rule_handler('Alias')
def emit_alias(rule, build_inputs, writer):
    writer.rule(
        target=path_str(rule.target.path),
        deps=(path_str(i.path) for i in rule.extra_deps),
        recipe=[],
        phony=True
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, writer):
    writer.rule(
        target=path_str(rule.target.path),
        deps=(path_str(i.path) for i in rule.extra_deps),
        recipe=rule.cmd,
        phony=True
    )
