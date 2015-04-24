import os
import re
from collections import Iterable, namedtuple, OrderedDict
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
            out.write('{}: '.format(escape_str(target)))
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
            out.write('.PHONY: {}\n'.format(escape_str(rule.target)))
        out.write('{target}:{deps}'.format(
            target=escape_str(rule.target),
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

srcdir_var = MakeVariable('srcdir')
def target_path(env, target):
    name = env.target_name(target)
    return path_join(srcdir_var, name) if target.is_source else name

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

def flags_vars(lang, value, writer):
    if value is None:
        return None, None

    global_flags = MakeVariable('GLOBAL_{}FLAGS'.format(lang.upper()))
    if not writer.has_variable(global_flags):
        writer.variable(global_flags, value)

    flags = MakeVariable('{}FLAGS'.format(lang.upper()))
    if not writer.has_variable(flags, target='%'):
        writer.variable(flags, global_flags, target='%')

    return global_flags, flags

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
                writer.variable(install_data, [install, '-m', '644'])
            return install_data

    def install_line(file):
        src = target_path(env, file)
        dst = path_join(
            prefix, file.install_dir, os.path.basename(env.target_name(file))
        )
        return [ install_cmd(file.install_kind), '-D', src, dst ]

    def mkdir_line(dir):
        src = path_join(target_path(env, dir), '*')
        dst = path_join(prefix, dir.install_dir)
        return ['mkdir', '-p', dst, '&&', 'cp', '-r', src, dst]

    recipe = ([install_line(i) for i in install_targets.files] +
              [mkdir_line(i) for i in install_targets.directories])
    writer.rule(target='install', deps=['all'], recipe=recipe, phony=True)

_seen_dirs = set() # TODO: Put this on the writer
def directory_rule(path, writer):
    if not path or path in _seen_dirs:
        return
    _seen_dirs.add(path)

    recipename = MakeVariable('RULE_MKDIR')
    if not writer.has_variable(recipename):
        writer.variable(recipename, [['mkdir', var('@')]], flavor='define')

    parent = os.path.dirname(path)
    order_only = [parent] if parent else None
    writer.rule(target=path, order_only=order_only, recipe=recipename)
    if parent:
        directory_rule(parent, writer)

@rule_handler('Compile')
def emit_object_file(rule, writer, env):
    compiler = env.compiler(rule.file.lang)
    recipename = MakeVariable('RULE_{}'.format(compiler.name.upper()))

    global_cflags, cflags = flags_vars(
        compiler.command_var, compiler.global_args, writer
    )
    if not writer.has_variable(recipename):
        esc = escaped_str
        writer.variable(recipename, [
            compiler.command(
                cmd=cmd_var(compiler, writer), input=var('<'), output=var('@'),
                dep=var('*') + '.d', args=cflags
            ),
            # Munge the depfile so that it works a little better...
            esc("@sed -e 's/.*://' -e 's/\\\\$$//' < $*.d | fmt -1 | \\"),
            esc("  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d")
        ], flavor='define')

    variables = {}
    if cflags:
        cflags_value = []
        if rule.target.in_shared_library:
            cflags_value.extend(compiler.library_args)
        cflags_value.extend(chain.from_iterable(
            compiler.include_dir(target_path(env, i)) for i in rule.include
        ))
        cflags_value.extend(rule.options)

        if cflags_value:
            variables[cflags] = [global_cflags] + cflags_value

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(target=env.target_name(rule.target),
                deps=[target_path(env, rule.file)], order_only=order_only,
                recipe=recipename, variables=variables)
    directory_rule(directory, writer)

    base = os.path.splitext(env.target_name(rule.file))[0]
    writer.include(base + '.d', optional=True)

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

    global_cflags, cflags = flags_vars(
        linker.command_var, linker.global_compile_args, writer
    )
    global_ldflags, ldflags = flags_vars(
        linker.link_var, linker.global_link_args, writer
    )
    if not writer.has_variable(recipename):
        writer.variable(recipename, [
            linker.command(
                cmd=cmd_var(linker, writer), input=var('1'), output=var('@'),
                compile_args=cflags, link_args=ldflags
            )
        ], flavor='define')

    lib_deps = (i for i in rule.libs if not i.is_source)
    deps = (target_path(env, i) for i in chain(rule.files, rule.deps, lib_deps))

    variables = {}
    if cflags:
        cflags_value = []
        cflags_value.extend(linker.mode_args)
        cflags_value.extend(rule.compile_options)

        if cflags_value:
            variables[cflags] = [global_cflags] + cflags_value

    if ldflags:
        ldflags_value = []
        ldflags_value.extend(chain.from_iterable(
            linker.link_lib(os.path.basename(i.name)) for i in rule.libs
        ))
        ldflags_value.extend(rule.link_options)

        if ldflags_value:
            variables[ldflags] = [global_ldflags] + ldflags_value

    directory = os.path.dirname(rule.target.name)
    order_only = [directory] if directory else None
    writer.rule(
        target=env.target_name(rule.target), deps=deps, order_only=order_only,
        recipe=MakeCall(
            recipename, (target_path(env, i) for i in rule.files)
        ),
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
