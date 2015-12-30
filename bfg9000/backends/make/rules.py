import os
from itertools import chain
from six.moves import filter as ifilter, cStringIO as StringIO

from . import version
from .syntax import *
from ... import path
from ... import safe_str
from ... import shell
from ... import iterutils
from ...builtins import find

Path = path.Path

priority = 2 if version is not None else 0
_rule_handlers = {}
_dir_sentinel = '.dir'


def rule_handler(rule_name):
    def decorator(fn):
        _rule_handlers[rule_name] = fn
        return fn
    return decorator


def write(env, build_inputs):
    buildfile = Makefile()
    buildfile.variable(path_vars[path.Root.srcdir], env.srcdir, Section.path)
    for i in path.InstallRoot:
        buildfile.variable(path_vars[i], env.install_dirs[i], Section.path)

    all_rule(build_inputs.get_default_targets(), buildfile)
    for e in build_inputs.edges:
        _rule_handlers[type(e).__name__](e, build_inputs, buildfile, env)
    install_rule(build_inputs.install_targets, buildfile, env)
    test_rule(build_inputs.tests, buildfile, env)
    directory_rule(buildfile, env)
    regenerate_rule(build_inputs.find_dirs, buildfile, env)

    with open(env.builddir.append('Makefile').string(), 'w') as out:
        buildfile.write(out)


def cmd_var(cmd, buildfile):
    name = cmd.command_var.upper()
    return buildfile.variable(name, cmd.command, Section.command, True)


def flags_vars(name, value, buildfile):
    name = name.upper()
    gflags = buildfile.variable('GLOBAL_' + name, value, Section.flags, True)
    flags = buildfile.target_variable(name, gflags, True)
    return gflags, flags


def all_rule(default_targets, buildfile):
    buildfile.rule(
        target='all',
        deps=default_targets,
        phony=True
    )


def install_rule(install_targets, buildfile, env):
    if not install_targets:
        return

    install = env.tool('install')
    mkdir_p = env.tool('mkdir_p')

    def install_line(file):
        kind = file.install_kind.upper()
        cmd = cmd_var(install, buildfile)

        if kind != 'PROGRAM':
            kind = 'DATA'
            cmd = [cmd] + install.data_args
        cmd = buildfile.variable('INSTALL_' + kind, cmd, Section.command, True)

        src = file.path
        dst = path.install_path(file.path, file.install_root)
        return install(cmd, src, dst)

    def mkdir_line(dir):
        src = dir.path
        dst = path.install_path(dir.path.parent(), dir.install_root)
        return mkdir_p.copy(cmd_var(mkdir_p, buildfile), src, dst)

    def post_install(file):
        if file.post_install:
            cmd = cmd_var(file.post_install, buildfile)
            return file.post_install(cmd, file)

    recipe = list(chain(
        (install_line(i) for i in install_targets.files),
        (mkdir_line(i) for i in install_targets.directories),
        ifilter(None, (post_install(i) for i in install_targets.files))
    ))
    buildfile.rule(
        target='install',
        deps='all',
        recipe=recipe,
        phony=True
    )


def test_rule(tests, buildfile, env):
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

    try:
        local_env = shell.local_env
    except AttributeError:
        setenv = env.tool('setenv')
        se_cmd = cmd_var(setenv, buildfile)
        local_env = lambda x: setenv(se_cmd, x)

    def build_commands(tests, collapse=False):
        def command(test, args=None):
            env_vars = local_env(test.env)
            subcmd = env_vars + [test.target] + test.options + (args or [])

            if collapse:
                out = Writer(StringIO())
                out.write_shell(subcmd)
                s = out.stream.getvalue()
                if len(subcmd) > 1:
                    s = shell.quote(s)
                return safe_str.escaped_str(s)
            return subcmd

        cmd, deps = [], []
        for i in tests:
            if type(i).__name__ == 'TestDriver':
                args, moredeps = build_commands(i.tests, True)
                if type(i.target).__name__ != 'SystemExecutable':
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


def directory_rule(buildfile, env):
    mkdir_p = env.tool('mkdir_p')
    pattern = Pattern(os.path.join('%', _dir_sentinel))
    path = Function('patsubst', pattern, Pattern('%'), var('@'), quoted=True)

    buildfile.rule(
        target=pattern,
        recipe=[
            silent(mkdir_p(cmd_var(mkdir_p, buildfile), path)),
            silent(['touch', qvar('@')])
        ]
    )


def regenerate_rule(find_dirs, buildfile, env):
    bfg9000 = env.tool('bfg9000')
    bfgpath = Path('build.bfg', path.Root.srcdir)
    extra_deps = []

    if find_dirs:
        find.write_depfile(env.builddir.append(find.depfile_name).string(),
                           'Makefile', find_dirs, makeify=True)
        buildfile.include(find.depfile_name)

    buildfile.rule(
        target=Path('Makefile'),
        deps=[bfgpath] + extra_deps,
        recipe=[bfg9000.regenerate(cmd_var(bfg9000, buildfile), Path('.'))]
    )


@rule_handler('Compile')
def emit_object_file(rule, build_inputs, buildfile, env):
    compiler = rule.builder
    recipename = Variable('RULE_{}'.format(compiler.rule_name.upper()))
    global_cflags, cflags = flags_vars(
        compiler.command_var + 'FLAGS',
        ( compiler.global_args +
          build_inputs.global_options.get(rule.file.lang, []) ),
        buildfile
    )

    path = rule.target.path
    target_dir = path.parent()

    variables = {}

    cflags_value = rule.options
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    if not buildfile.has_variable(recipename):
        cmd = cmd_var(compiler, buildfile)
        command_kwargs = {}
        recipe_extra = []

        if compiler.deps_flavor == 'gcc':
            depfixer = env.tool('depfixer')
            command_kwargs['deps'] = deps = qvar('@') + '.d'
            df_cmd = cmd_var(env.tool('depfixer'), buildfile)
            recipe_extra = [silent(depfixer(df_cmd, deps))]
        elif compiler.deps_flavor == 'msvc':
            command_kwargs['deps'] = True

        buildfile.define(recipename, [
            compiler(cmd=cmd, input=qvar('<'), output=qvar('@'), args=cflags,
                     **command_kwargs),
        ] + recipe_extra)

    buildfile.rule(
        target=path,
        deps=[rule.file] + rule.extra_deps,
        order_only=[target_dir.append(_dir_sentinel)] if target_dir else None,
        recipe=recipename,
        variables=variables
    )
    buildfile.include(path.addext('.d'), optional=True)


@rule_handler('Link')
def emit_link(rule, build_inputs, buildfile, env):
    linker = rule.builder
    recipename = Variable('RULE_{}'.format(linker.rule_name.upper()))
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'FLAGS',
        linker.global_args + build_inputs.global_link_options,
        buildfile
    )

    variables = {}
    command_kwargs = {}

    ldflags_value = linker.mode_args + rule.options
    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    if linker.mode != 'static_library':
        global_ldlibs, ldlibs = flags_vars(
            linker.link_var + 'LIBS', linker.global_libs, buildfile
        )
        command_kwargs['libs'] = ldlibs
        if rule.lib_options:
            variables[ldlibs] = [global_ldlibs] + rule.lib_options

    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [
            linker(cmd=cmd_var(linker, buildfile), input=var('1'),
                   output=var('2'), args=ldflags, **command_kwargs)
        ])

    recipe = Call(recipename, rule.files, rule.target.path)
    if len(rule.target.all) > 1:
        target = rule.target.path.addext('.stamp')
        buildfile.rule(target=rule.target.all, deps=[target])
        recipe = [recipe, silent([ 'touch', var('@') ])]
    else:
        target = rule.target

    dirs = iterutils.uniques(i.path.parent() for i in rule.target.all)
    buildfile.rule(
        target=target,
        deps=rule.files + rule.libs + rule.extra_deps,
        order_only=[i.append(_dir_sentinel) for i in dirs if i],
        recipe=recipe,
        variables=variables
    )


@rule_handler('Alias')
def emit_alias(rule, build_inputs, buildfile, env):
    buildfile.rule(
        target=rule.target,
        deps=rule.extra_deps,
        phony=True
    )


@rule_handler('Command')
def emit_command(rule, build_inputs, buildfile, env):
    # Join all the commands onto one line so that users can use 'cd' and such.
    out = Writer(StringIO())
    env_vars = shell.global_env(rule.env)
    for line in shell.join_commands(chain(env_vars, rule.cmds)):
        out.write_shell(line)

    buildfile.rule(
        target=rule.target,
        deps=rule.extra_deps,
        recipe=[safe_str.escaped_str(out.stream.getvalue())],
        phony=True
    )
