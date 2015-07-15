import operator
import os
import re
from cStringIO import StringIO
from collections import namedtuple, OrderedDict
from itertools import chain

from .. import path
from .. import safe_str
from .. import shell
from .. import utils
from ..builtins import find

Path = path.Path

_rule_handlers = {}
def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['targets', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

class MakeWriter(object):
    def __init__(self, stream):
        self.stream = stream

    @staticmethod
    def escape_str(string, syntax):
        def repl(match):
            return match.group(1) * 2 + '\\' + match.group(2)
        result = string.replace('$', '$$')

        if syntax == 'target':
            return re.sub(r'(\\*)([#?*\[\]~\s%])', repl, result)
        elif syntax == 'dependency':
            return re.sub(r'(\\*)([#?*\[\]~\s|%])', repl, result)
        elif syntax == 'function':
            return shell.quote(re.sub(',', '$,', result))
        elif syntax == 'shell':
            return result
        else:
            raise ValueError("unknown syntax '{}'".format(syntax))

    def write_literal(self, string):
        self.stream.write(string)

    def write(self, thing, syntax, shell_quote=True):
        thing = safe_str.safe_str(thing)
        shelly = syntax in ['function', 'shell']

        if isinstance(thing, safe_str.escaped_str):
            self.write_literal(thing.string)
        elif isinstance(thing, basestring):
            thing = self.escape_str(thing, syntax)
            if shelly and shell_quote:
                thing = shell.quote(thing)
            self.write_literal(thing)
        elif isinstance(thing, safe_str.jbos):
            for i in thing.bits:
                self.write(i, syntax, shell_quote)
        elif isinstance(thing, Path):
            self.write(thing.realize(_path_vars, shelly), syntax, shell_quote)
        else:
            raise TypeError(type(thing))

    def write_each(self, things, syntax, delim=' ', prefix=None, suffix=None):
        for tween, i in utils.tween(things, delim, prefix, suffix):
            self.write_literal(i) if tween else self.write(i, syntax)

    def write_shell(self, thing):
        if utils.isiterable(thing):
            self.write_each(thing, 'shell')
        else:
            self.write(thing, 'shell', shell_quote=False)

class Pattern(object):
    def __init__(self, path):
        if len(re.findall(r'([^\\]|^)(\\\\)*%', path)) != 1:
            raise ValueError('exactly one % required')
        self.path = path

    def use(self):
        bits = re.split(r'%', self.path)
        delim = safe_str.escaped_str('%')
        return reduce(operator.add, utils.tween(bits, delim, flag=False))

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

    def __hash__(self):
        return hash(self.path)

    def __cmp__(self, rhs):
        return cmp(self.path, rhs.path)

    def __add__(self, rhs):
        return self.use() + rhs

    def __radd__(self, lhs):
        return lhs + self.use()

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

    def __cmp__(self, rhs):
        return cmp(self.name, rhs.name)

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
        out = MakeWriter(StringIO())
        prefix = '$(' + self.name + ' '
        for tween, i in utils.tween(self.args, ',', prefix, ')'):
            if tween:
                out.write_literal(i)
            else:
                out.write_each(utils.iterate(i), syntax='function')
        return safe_str.escaped_str(out.stream.getvalue())

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

_path_vars = {
    Path.srcdir:     var('srcdir'),
    Path.builddir:   None,
    Path.prefix:     var('prefix'),
    Path.bindir:     var('bindir'),
    Path.libdir:     var('libdir'),
    Path.includedir: var('includedir'),
}

class Makefile(object):
    def __init__(self):
        # TODO: Sort variables in some useful order.
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict({Pattern('%'): OrderedDict()})
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
            raise ValueError("variable '{}' already exists".format(name.name))

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
            raise ValueError('must have at least one target')
        for i in targets:
            if self.has_rule(i):
                raise ValueError("rule for '{}' already exists".format(i))
            self._targets.add(i)
        self._rules.append(MakeRule(
            targets, utils.listify(deps), utils.listify(order_only), recipe,
            real_variables, phony
        ))

    def has_rule(self, name):
        return name in self._targets

    def _write_variable(self, out, name, value, flavor, target=None):
        operator = ' := ' if flavor == 'simple' else ' = '
        if target:
            out.write(target, syntax='target')
            out.write_literal(': ')
        out.write_literal(name.name + operator)
        out.write_shell(value)
        out.write_literal('\n')

    def _write_define(self, out, name, value):
        out.write_literal('define ' + name.name + '\n')
        for line in value:
            out.write_shell(line)
            out.write_literal('\n')
        out.write_literal('endef\n\n')

    def _write_rule(self, out, rule):
        if rule.variables:
            for target in rule.targets:
                for name, value in rule.variables.iteritems():
                    self._write_variable(out, name, value, 'simple',
                                         target=target)

        if rule.phony:
            out.write_literal('.PHONY: ')
            out.write_each(rule.targets, syntax='dependency')
            out.write_literal('\n')

        out.write_each(rule.targets, syntax='target')
        out.write_literal(':')
        out.write_each(rule.deps, syntax='dependency', prefix=' ')
        out.write_each(rule.order_only, syntax='dependency', prefix=' | ')

        if (isinstance(rule.recipe, MakeVariable) or
            isinstance(rule.recipe, MakeFunc)):
            out.write_literal(' ; ')
            out.write_shell(rule.recipe)
        elif rule.recipe is not None:
            for cmd in rule.recipe:
                out.write_literal('\n\t')
                out.write_shell(cmd)
        out.write_literal('\n\n')

    def write(self, out):
        out = MakeWriter(out)

        # Don't let make use built-in suffix rules.
        out.write_literal('.SUFFIXES:\n\n')

        for name, value in self._global_variables.iteritems():
            self._write_variable(out, name, value[0], value[1])
        if self._global_variables:
            out.write_literal('\n')

        newline = False
        for target, each in self._target_variables.iteritems():
            for name, value in each.iteritems():
                newline = True
                self._write_variable(out, name, value[0], value[1], target)
        if newline:
            out.write_literal('\n')

        for name, value in self._defines.iteritems():
            self._write_define(out, name, value)

        for r in self._rules:
            self._write_rule(out, r)

        for i in self._includes:
            out.write_literal(('-' if i.optional else '') + 'include ')
            out.write(i.name, syntax='target')
            out.write_literal('\n')

def write(env, build_inputs):
    buildfile = Makefile()
    buildfile.variable(_path_vars['srcdir'], env.srcdir)
    for i in [Path.prefix, Path.bindir, Path.libdir, Path.includedir]:
        buildfile.variable(_path_vars[i], env.install_dirs[i])

    all_rule(build_inputs.get_default_targets(), buildfile)
    install_rule(build_inputs.install_targets, buildfile, env)
    test_rule(build_inputs.tests, buildfile)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, buildfile)
    directory_rule(buildfile)
    regenerate_rule(build_inputs.find_dirs, buildfile, env)

    with open(os.path.join(env.builddir, 'Makefile'), 'w') as out:
        buildfile.write(out)

def cmd_var(compiler, buildfile):
    var = MakeVariable(compiler.command_var.upper())
    if not buildfile.has_variable(var):
        buildfile.variable(var, compiler.command_name)
    return var

def flags_vars(name, value, buildfile):
    name = name.upper()
    global_flags = MakeVariable('GLOBAL_{}'.format(name))
    if not buildfile.has_variable(global_flags):
        buildfile.variable(global_flags, value)

    flags = MakeVariable(name)
    if not buildfile.has_variable(flags, target=Pattern('%')):
        buildfile.variable(flags, global_flags, target=Pattern('%'))

    return global_flags, flags

def all_rule(default_targets, buildfile):
    buildfile.rule(
        target='all',
        deps=default_targets,
        phony=True
    )

# TODO: Write a better `install` program to simplify this
def install_rule(install_targets, buildfile, env):
    if not install_targets:
        return

    def install_cmd(kind):
        install = MakeVariable('INSTALL')
        if not buildfile.has_variable(install):
            buildfile.variable(install, 'install')

        if kind == 'program':
            install_program = MakeVariable('INSTALL_PROGRAM')
            if not buildfile.has_variable(install_program):
                buildfile.variable(install_program, install)
            return install_program
        else:
            install_data = MakeVariable('INSTALL_DATA')
            if not buildfile.has_variable(install_data):
                buildfile.variable(install_data, [install, '-m', '644'])
            return install_data

    def install_line(file):
        src = file.path
        dst = path.install_path(file.path, file.install_root)
        return [install_cmd(file.install_kind), '-D', src, dst]

    def mkdir_line(dir):
        src = dir.path.append('*')
        dst = path.install_path(dir.path.parent(), dir.install_root)
        return 'mkdir -p ' + dst + ' && cp -r ' + src + ' ' + dst

    post_install = filter(None, (getattr(i, 'post_install', None)
                                 for i in install_targets.files))

    recipe = ([install_line(i) for i in install_targets.files] +
              [mkdir_line(i) for i in install_targets.directories] +
              post_install)
    buildfile.rule(
        target='install',
        deps='all',
        recipe=recipe,
        phony=True
    )

def test_rule(tests, buildfile):
    if not tests:
        return

    deps = []
    if tests.targets:
        buildfile.rule(
            target='tests',
            deps=tests.targets,
            phony=True
        )
        deps.append('tests')
    deps.extend(tests.extra_deps)

    def build_commands(tests, collapse=False):
        cmd, deps = [], []
        def command(test, args=None):
            env = [safe_str.jbos(k, '=', v) for k, v in test.env.iteritems()]
            subcmd = env + [test.target] + test.options + (args or [])
            if collapse:
                out = MakeWriter(StringIO())
                out.write_shell(subcmd)
                return safe_str.escaped_str(shell.quote(out.stream.getvalue()))
            return subcmd

        for i in tests:
            if type(i).__name__ == 'TestDriver':
                args, moredeps = build_commands(i.tests, True)
                if i.target.creator:
                    deps.append(i.target)
                deps.extend(moredeps)
                cmd.append(command(i, args))
            else:
                cmd.append(command(i))
        return cmd, deps

    recipe, moredeps = build_commands(tests.tests)
    buildfile.rule(
        target='test',
        deps=deps + moredeps,
        recipe=recipe,
        phony=True
    )

dir_sentinel = '.dir'
def directory_rule(buildfile):
    # XXX: `mkdir -p` isn't safe (or valid!) on all platforms.
    buildfile.rule(
        target=Pattern(os.path.join('%', dir_sentinel)),
        recipe=[
            ['@mkdir', '-p', MakeFunc('dir', var('@'))],
            ['@touch', var('@')]
        ]
    )

def regenerate_rule(find_dirs, buildfile, env):
    bfgpath = Path('build.bfg', Path.srcdir)
    extra_deps = []

    if find_dirs:
        find.write_depfile(os.path.join(env.builddir, find.depfile_name),
                           'Makefile', find_dirs, makeify=True)
        buildfile.include(find.depfile_name)

    buildfile.rule(
        target=Path('Makefile'),
        deps=[bfgpath] + extra_deps,
        recipe=[[env.bfgpath, '--regenerate', '.']]
    )

@rule_handler('Compile')
def emit_object_file(rule, build_inputs, buildfile):
    compiler = rule.builder
    recipename = MakeVariable('RULE_{}'.format(compiler.name.upper()))
    global_cflags, cflags = flags_vars(
        compiler.command_var + 'FLAGS',
        compiler.global_args +
          build_inputs.global_options.get(rule.file.lang, []),
        buildfile
    )

    path = rule.target.path
    target_dir = path.parent()

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

    if not buildfile.has_variable(recipename):
        command_kwargs = {}
        recipe_extra = []
        if compiler.deps_flavor == 'gcc':
            command_kwargs['deps'] = deps = var('@') + '.d'
            # Munge the depfile so that it works a little better. See
            # <http://scottmcpeak.com/autodepend/autodepend.html> for a
            # discussion of how this works.
            recipe_extra = [
                r"@sed -e 's/.*://' -e 's/\\$//' < " + deps + ' | fmt -1 | \\',
                "  sed -e 's/^ *//' -e 's/$/:/' >> " + deps
            ]
        elif compiler.deps_flavor == 'msvc':
            command_kwargs['deps'] = True

        buildfile.variable(recipename, [
            compiler.command(
                cmd=cmd_var(compiler, buildfile), input=var('<'),
                output=var('@'), args=cflags, **command_kwargs
            ),
        ] + recipe_extra, flavor='define')

    buildfile.rule(
        target=path,
        deps=[rule.file] + rule.extra_deps,
        order_only=[target_dir.append(dir_sentinel)] if target_dir else None,
        recipe=recipename,
        variables=variables
    )
    buildfile.include(path.addext('.d'), optional=True)

@rule_handler('Link')
def emit_link(rule, build_inputs, buildfile):
    linker = rule.builder
    recipename = MakeVariable('RULE_{}'.format(linker.name.upper()))
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'FLAGS',
        linker.global_args + build_inputs.global_link_options,
        buildfile
    )

    variables = {}
    command_kwargs = {}
    ldflags_value = list(linker.mode_args)

    # Get the path for the DLL if this is a Windows build.
    path = utils.first(rule.target).path

    if linker.mode != 'static_library':
        ldflags_value.extend(rule.options)
        ldflags_value.extend(linker.lib_dirs(rule.libs))
        ldflags_value.extend(linker.rpath(rule.libs, path.parent()))
        ldflags_value.extend(linker.import_lib(rule.target))

        global_ldlibs, ldlibs = flags_vars(
            linker.link_var + 'LIBS', linker.global_libs, buildfile
        )
        command_kwargs['libs'] = ldlibs
        if rule.libs:
            libs = sum((linker.link_lib(i) for i in rule.libs), [])
            variables[ldlibs] = [global_ldlibs] + libs

    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    if not buildfile.has_variable(recipename):
        buildfile.variable(recipename, [
            linker.command(
                cmd=cmd_var(linker, buildfile), input=var('1'), output=var('2'),
                args=ldflags, **command_kwargs
            )
        ], flavor='define')

    recipe = MakeCall(recipename, rule.files, path)
    if utils.isiterable(rule.target):
        target = path.addext('.stamp')
        buildfile.rule(target=rule.target, deps=[target])
        recipe = [recipe, ['@touch', var('@')]]
    else:
        target = path

    dirs = utils.uniques(i.path.parent() for i in utils.iterate(rule.target))
    lib_deps = [i for i in rule.libs if i.creator]
    buildfile.rule(
        target=target,
        deps=rule.files + lib_deps + rule.extra_deps,
        order_only=[i.append(dir_sentinel) for i in dirs if i],
        recipe=recipe,
        variables=variables
    )

@rule_handler('Alias')
def emit_alias(rule, build_inputs, buildfile):
    buildfile.rule(
        target=rule.target,
        deps=rule.extra_deps,
        phony=True
    )

@rule_handler('Command')
def emit_command(rule, build_inputs, buildfile):
    buildfile.rule(
        target=rule.target,
        deps=rule.extra_deps,
        recipe=rule.cmds,
        phony=True
    )
