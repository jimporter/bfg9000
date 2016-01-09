from .writer import *
from .syntax import *
from ... import path

Path = path.Path


@rule_handler('Compile')
def emit_object_file(rule, build_inputs, buildfile):
    compiler = rule.builder
    global_cflags, cflags = flags_vars(
        compiler.command_var + 'flags',
        ( compiler.global_args +
          build_inputs.global_options.get(rule.file.lang, []) ),
        buildfile
    )

    variables = {}

    cflags_value = rule.options
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    if not buildfile.has_rule(compiler.rule_name):
        command_kwargs = {}
        depfile = None
        deps = None
        if compiler.deps_flavor == 'gcc':
            deps = 'gcc'
            command_kwargs['deps'] = depfile = var('out') + '.d'
        elif compiler.deps_flavor == 'msvc':
            deps = 'msvc'
            command_kwargs['deps'] = True

        buildfile.rule(name=compiler.rule_name, command=compiler(
            cmd=cmd_var(compiler, buildfile), input=var('in'),
            output=var('out'), args=cflags, **command_kwargs
        ), depfile=depfile, deps=deps)

    buildfile.build(
        output=rule.target,
        rule=compiler.rule_name,
        inputs=[rule.file],
        implicit=rule.extra_deps,
        variables=variables
    )


@rule_handler('Link')
def emit_link(rule, build_inputs, buildfile):
    linker = rule.builder
    global_ldflags, ldflags = flags_vars(
        linker.link_var + 'flags',
        linker.global_args + build_inputs.global_link_options,
        buildfile
    )

    variables = {}
    command_kwargs = {}

    ldflags_value = linker.mode_args + rule.options
    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

    variables[var('output')] = rule.target.path

    if linker.mode != 'static_library':
        global_ldlibs, ldlibs = flags_vars(
            linker.link_var + 'libs', linker.global_libs, buildfile
        )
        command_kwargs['libs'] = ldlibs
        if rule.lib_options:
            variables[ldlibs] = [global_ldlibs] + rule.lib_options

    if not buildfile.has_rule(linker.rule_name):
        buildfile.rule(name=linker.rule_name, command=linker(
            cmd=cmd_var(linker, buildfile), input=var('in'),
            output=var('output'), args=ldflags, **command_kwargs
        ))

    buildfile.build(
        output=rule.target.all,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=rule.libs + rule.extra_deps,
        variables=variables
    )


@rule_handler('Alias')
def emit_alias(rule, build_inputs, buildfile):
    buildfile.build(
        output=rule.target,
        rule='phony',
        inputs=rule.extra_deps
    )


@rule_handler('Command')
def emit_command(rule, build_inputs, buildfile):
    command_build(
        buildfile,
        output=rule.target,
        inputs=rule.extra_deps,
        commands=rule.cmds,
        env=rule.env
    )
