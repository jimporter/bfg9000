from itertools import chain
from six.moves import cStringIO as StringIO

from .writer import *
from .syntax import *
from ... import path
from ... import safe_str
from ... import shell
from ... import iterutils

Path = path.Path


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
        order_only=[target_dir.append(dir_sentinel)] if target_dir else None,
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
        order_only=[i.append(dir_sentinel) for i in dirs if i],
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
