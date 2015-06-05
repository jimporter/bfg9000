import os
import re
from cStringIO import StringIO
from collections import Iterable, namedtuple, OrderedDict
from itertools import chain

import safe_str
import shell
import utils
from path import Path, phony_path

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['targets', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

class MakeVariable(object):
    def __init__(self, name):
        self.name = re.sub(r'[\s:#=]', '_', name)

    def use(self):
        fmt = '${}' if len(self.name) == 1 else '$({})'
        return safe_str.escaped_str(fmt.format(self.name))

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __ne__(self, rhs):
        return self.name != rhs.name

    def __add__(self, rhs):
        return self.use() + rhs

    def __radd__(self, lhs):
        return lhs + self.use()

var = MakeVariable

class MakeFunc(object):
    def __init__(self, name, *args):
        self.name = name
        self.args = args

    def use(self):
        out = StringIO()
        MakeWriter._write_literal(out, '$(' + self.name + ' ')
        for tween, i in utils.tween(self.args, ','):
            if tween:
                MakeWriter._write_literal(out, i)
            else:
                MakeWriter._write_each(out, utils.iterate(i), syntax='function')
        MakeWriter._write_literal(out, ')')
        return safe_str.escaped_str(out.getvalue())

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

class MakeCall(MakeFunc):
    def __init__(self, func, *args):
        if not isinstance(func, MakeVariable):
            func = MakeVariable(func)
        MakeFunc.__init__(self, 'call', func.name, *args)

class MakeWriter(object):
    def __init__(self):
        # TODO: Sort variables in some useful order.
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict({phony_path('%'): OrderedDict()})
        self._defines = OrderedDict()

        self._rules = []
        self._targets = set()
        self._includes = []

        # Necessary for escaping commas in function calls.
        self.variable(',', ',')

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

        targets = utils.listify(target)
        if len(targets) == 0:
            raise RuntimeError('must have at least one target')
        for i in targets:
            if self.has_rule(i):
                raise RuntimeError('rule for "{}" already exists'.format(i))
            self._targets.add(i)
        self._rules.append(MakeRule(
            targets, utils.listify(deps), utils.listify(order_only), recipe,
            real_variables, phony
        ))

    def has_rule(self, name):
        return name in self._targets

    @classmethod
    def escape_str(cls, string, syntax):
        def repl(match):
            return match.group(1) * 2 + '\\' + match.group(2)
        result = string.replace('$', '$$')

        if syntax == 'target':
            return re.sub(r'(\\*)([#?*\[\]~\s])', repl, result)
        if syntax == 'dependency':
            return re.sub(r'(\\*)([#?*\[\]~\s|])', repl, result)
        elif syntax == 'shell':
            return shell.quote(result)
        elif syntax == 'function':
            return shell.quote(re.sub(',', '$,', result))
        else:
            raise RuntimeError('unknown syntax "{}"'.format(syntax))

    @classmethod
    def _write_literal(cls, out, string):
        out.write(string)

    @classmethod
    def _write(cls, out, thing, syntax):
        # TODO: Remove this once paths have _safe_str.
        if isinstance(thing, Path):
            thing = path_str(thing)
        thing = safe_str.safe_str(thing)

        if isinstance(thing, basestring):
            out.write(cls.escape_str(thing, syntax))
        elif isinstance(thing, safe_str.escaped_str):
            out.write(thing.string)
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

    def _write_variable(self, out, name, value, flavor, target=None):
        operator = ' := ' if flavor == 'simple' else ' = '
        if target:
            self._write(out, target, syntax='target')
            self._write_literal(out, ': ')
        self._write_literal(out, name.name + operator)
        self._write_each(out, utils.iterate(value), syntax='shell')
        self._write_literal(out, '\n')

    def _write_define(self, out, name, value):
        self._write_literal(out, 'define ' + name.name + '\n')
        for i in value:
            self._write_each(out, i, syntax='shell')
            self._write_literal(out, '\n')
        self._write_literal(out, 'endef\n\n')

    def _write_rule(self, out, rule):
        if rule.variables:
            for target in rule.targets:
                for name, value in rule.variables.iteritems():
                    self._write_variable(out, name, value, 'simple',
                                         target=target)

        if rule.phony:
            self._write_literal(out, '.PHONY: ')
            self._write_each(out, rule.targets, syntax='dependency')
            self._write_literal(out, '\n')

        self._write_each(out, rule.targets, syntax='target')
        self._write_literal(out, ':')
        self._write_each(out, rule.deps, syntax='dependency', prefix=' ')
        self._write_each(out, rule.order_only, syntax='dependency',
                         prefix=' | ')

        if (isinstance(rule.recipe, MakeVariable) or
            isinstance(rule.recipe, MakeFunc)):
            self._write_literal(out, ' ; ')
            self._write(out, rule.recipe, syntax='shell')
        elif rule.recipe is not None:
            for cmd in rule.recipe:
                self._write_literal(out, '\n\t')
                self._write_each(out, cmd, syntax='shell')
        self._write_literal(out, '\n\n')

    def write(self, out):
        # Don't let make use built-in suffix rules.
        self._write_literal(out, '.SUFFIXES:\n\n')

        for name, value in self._global_variables.iteritems():
            self._write_variable(out, name, value[0], value[1])
        if self._global_variables:
            self._write_literal(out, '\n')

        newline = False
        for target, each in self._target_variables.iteritems():
            for name, value in each.iteritems():
                newline = True
                self._write_variable(out, name, value[0], value[1], target)
        if newline:
            self._write_literal(out, '\n')

        for name, value in self._defines.iteritems():
            self._write_define(out, name, value)

        for r in self._rules:
            self._write_rule(out, r)

        for i in self._includes:
            self._write_literal(out, ('-' if i.optional else '') + 'include ')
            self._write(out, i.name, syntax='target')
            self._write_literal(out, '\n')

_path_vars = {
    'srcdir': MakeVariable('srcdir'),
    'prefix': MakeVariable('prefix'),
}
def path_str(path, form='local_path'):
    source, pathname = getattr(path, form)()
    if source:
        return _path_vars[source] + os.sep + pathname
    else:
        return pathname

def write(env, build_inputs):
    writer = MakeWriter()
    writer.variable(_path_vars['srcdir'], env.srcdir)

    all_rule(build_inputs.get_default_targets(), writer)
    install_rule(build_inputs.install_targets, writer, env)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, writer)
    directory_rule(writer)
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
    if not writer.has_variable(flags, target=phony_path('%')):
        writer.variable(flags, global_flags, target=phony_path('%'))

    return global_flags, flags

def all_rule(default_targets, writer):
    writer.rule(
        target=phony_path('all'),
        deps=(i.path for i in default_targets)
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
        e = safe_str.escaped_str
        src = path_str(dir.path) + os.sep + e('*')
        dst = path_str(dir.path.parent(), 'install_path')
        return ['mkdir', '-p', dst, e('&&'), 'cp', '-r', src, dst]

    recipe = ([install_line(i) for i in install_targets.files] +
              [mkdir_line(i) for i in install_targets.directories])
    writer.rule(
        target=phony_path('install'),
        deps=phony_path('all'),
        recipe=recipe,
        phony=True
    )

dir_sentinel = '.dir'
def directory_rule(writer):
    # XXX: `mkdir -p` isn't safe (or valid!) on all platforms.
    writer.rule(
        target=phony_path(os.path.join('%', dir_sentinel)),
        recipe=[
            ['@mkdir', '-p', MakeFunc('dir', var('@'))],
            ['@touch', var('@')]
        ]
    )

def regenerate_rule(writer, env):
    writer.rule(
        target=phony_path('Makefile'),
        deps=Path('build.bfg', Path.srcdir, Path.basedir),
        recipe=[[env.bfgpath, '--regenerate', '.']]
    )

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
        e = safe_str.escaped_str
        writer.variable(recipename, [
            compiler.command(
                cmd=cmd_var(compiler, writer), input=var('<'), output=var('@'),
                dep=depfile, args=cflags
            ),
            # Munge the depfile so that it works a little better...
            ['@sed', '-e', 's/.*://', '-e', r's/\\$//', e('<'), depfile, e('|'),
             'fmt', '-1', e('| \\')],
            [e(' '), 'sed', '-e', 's/^ *//', '-e', 's/$/:/', e('>>'), depfile]
        ], flavor='define')

    writer.rule(
        target=path,
        deps=(i.path for i in chain([rule.file], rule.extra_deps)),
        order_only=[target_dir.append(dir_sentinel)] if target_dir else None,
        recipe=recipename,
        variables=variables
    )
    writer.include(path.addext('.d'), optional=True)

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

    variables = {}
    command_kwargs = {}
    ldflags_value = linker.mode_args[:]
    lib_deps = [i for i in rule.libs if i.creator]

    # TODO: Create a more flexible way of determining when to use these options?
    if linker.mode != 'static_library':
        lib_dirs = set(path_str(i.path.parent()) for i in lib_deps)
        target_dirname = path_str(target_dir)

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
        target=path,
        deps=(i.path for i in chain(rule.files, lib_deps, rule.extra_deps)),
        order_only=[target_dir.append(dir_sentinel)] if target_dir else None,
        recipe=MakeCall(recipename, (path_str(i.path) for i in rule.files)),
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, build_inputs, writer):
    writer.rule(
        target=rule.target.path,
        deps=(i.path for i in rule.extra_deps),
        phony=True
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, writer):
    writer.rule(
        target=rule.target.path,
        deps=(i.path for i in rule.extra_deps),
        recipe=rule.cmd,
        phony=True
    )
