from collections import defaultdict
from six import string_types

from . import builtin
from .. import options as opts
from .file_types import local_file
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import first, iterate, uniques
from ..path import Path, Root
from ..shell import posix as pshell

build_input('compile_options')(lambda build_inputs, env: defaultdict(list))


class ObjectFiles(list):
    def __init__(self, builtins, build, env, files, **kwargs):
        list.__init__(self, (builtins['_make_object_file'](i, **kwargs)
                             for i in iterate(files)))

    def __getitem__(self, key):
        if isinstance(key, string_types):
            key = Path(key, Root.srcdir)
        elif isinstance(key, File):
            key = key.path

        if isinstance(key, Path):
            for i in self:
                if i.creator and i.creator.file.path == key:
                    return i
            raise IndexError("{!r} not found".format(key))
        else:
            return list.__getitem__(self, key)


class Compile(Edge):
    desc_verb = 'compile'

    def __init__(self, builtins, build, env, name, includes=None, pch=None,
                 libs=None, packages=None, options=None, lang=None,
                 extra_deps=None, description=None):
        self.header_files = []
        self.includes = []
        for i in iterate(includes):
            if isinstance(i, HeaderFile):
                self.header_files.append(i)
            self.includes.append(builtins['header_directory'](i))

        # Don't bother handling forward_opts from libs now, since the only
        # languages that need libs during compilation don't support static
        # linking anyway.
        if self.compiler.needs_libs:
            self.libs = [builtins['library'](i, lang=lang)
                         for i in iterate(libs)]

        self.packages = [builtins['package'](i) for i in iterate(packages)]
        self.user_options = pshell.listify(options, type=opts.option_list)

        if pch and not self.compiler.accepts_pch:
            raise TypeError('pch not supported for this compiler')
        self.pch = builtins['precompiled_header'](
            pch, file=pch, includes=includes, packages=self.packages,
            options=self.user_options, lang=lang
        ) if pch else None

        extra_options = self.compiler.pre_build(build, name, self)
        output = self.compiler.output_file(name, self)
        primary = first(output)

        lib_options = None
        if self.compiler.needs_libs:
            lib_options = (opts.lib(i) for i in self.libs)
        self._internal_options = opts.option_list(
            (i.compile_options(self.compiler, output) for i in self.packages),
            (opts.include_dir(i) for i in self.includes),
            opts.pch(self.pch) if self.pch else None,
            lib_options, extra_options
        )

        options = self.options
        public_output = self.compiler.post_build(build, options, output, self)
        primary.post_install = self.compiler.post_install(options, output,
                                                          self)

        Edge.__init__(self, build, output, public_output, extra_deps,
                      description)

    def add_extra_options(self, options):
        self._internal_options.extend(options)
        # PCH files should always be built with the same options as files using
        # them, so forward the extra options onto the PCH if it exists.
        if self.pch and hasattr(self.pch.creator, 'add_extra_options'):
            self.pch.creator.add_extra_options(options)

    @property
    def options(self):
        return self._internal_options + self.user_options

    @property
    def flags(self):
        return self.compiler.flags(self.options, self.raw_output)


class CompileSource(Compile):
    def __init__(self, builtins, build, env, name, file, **kwargs):
        self.file = builtins['source_file'](file, lang=kwargs.get('lang'))
        if name is None:
            name = self.file.path.stripext().suffix

        if self.file.lang is None:
            raise ValueError("unable to determine language for file {!r}"
                             .format(self.file.path))
        self.compiler = env.builder(self.file.lang).compiler
        Compile.__init__(self, builtins, build, env, name, **kwargs)


class CompileHeader(Compile):
    desc_verb = 'compile-header'

    def __init__(self, builtins, build, env, name, file, **kwargs):
        self.file = builtins['header_file'](file, lang=kwargs.get('lang'))
        if name is None:
            name = self.file.path.suffix

        source = kwargs.pop('source', None)
        self.pch_source = builtins['source_file'](
            source, lang=self.file.lang
        ) if source else None

        if self.file.lang is None:
            raise ValueError("unable to determine language for file {!r}"
                             .format(self.file.path))
        self.compiler = env.builder(self.file.lang).pch_compiler
        Compile.__init__(self, builtins, build, env, name, **kwargs)


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFile, in_type=string_types + (type(None),))
def object_file(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        return local_file(build, ObjectFile, name, params, kwargs)
    return CompileSource(builtins, build, env, name, file,
                         **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFile, in_type=string_types + (SourceFile,))
def _make_object_file(builtins, build, env, file, **kwargs):
    return CompileSource(builtins, build, env, None, file,
                         **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFiles, in_type=object)
def object_files(builtins, build, env, files, **kwargs):
    return ObjectFiles(builtins, build, env, files, **kwargs)


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(PrecompiledHeader, in_type=string_types + (type(None),))
def precompiled_header(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        params = [('lang', 'c')]
        return local_file(build, PrecompiledHeader, name, params, kwargs)
    return CompileHeader(builtins, build, env, name, file,
                         **kwargs).public_output


@builtin.function('build_inputs')
def global_options(build, options, lang):
    for i in iterate(lang):
        build['compile_options'][i].extend(pshell.listify(
            options, type=opts.option_list
        ))


def _get_flags(backend, rule, build_inputs, buildfile):
    variables = {}
    cmd_kwargs = {}

    compiler = rule.compiler
    if hasattr(compiler, 'flags_var'):
        global_cflags, cflags = backend.flags_vars(
            compiler.flags_var,
            ( compiler.global_flags +
              compiler.flags(build_inputs['compile_options'][compiler.lang]) ),
            buildfile
        )
        cmd_kwargs['flags'] = cflags
        flags = rule.flags
        if flags:
            variables[cflags] = [global_cflags] + flags

    return variables, cmd_kwargs


@make.rule_handler(CompileSource, CompileHeader)
def make_compile(rule, build_inputs, buildfile, env):
    compiler = rule.compiler
    variables, cmd_kwargs = _get_flags(make, rule, build_inputs, buildfile)

    output_params = []
    if len(rule.output) == 1:
        output_vars = make.qvar('@')
    else:
        output_vars = []
        for i in range(compiler.num_outputs):
            v = make.var(str(i + 1))
            output_vars.append(v)
            output_params.append(rule.output[i])

    recipename = make.var('RULE_{}'.format(compiler.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        recipe_extra = []

        # Only GCC-style depfiles are supported by Make.
        if compiler.deps_flavor == 'gcc':
            depfixer = env.tool('depfixer')
            cmd_kwargs['deps'] = deps = first(output_vars) + '.d'
            recipe_extra = [make.Silent(depfixer(deps))]

            depfile = rule.output[0].path.addext('.d')
            build_inputs.add_target(File(depfile))
            buildfile.include(depfile, optional=True)

        buildfile.define(recipename, [compiler(
            make.qvar('<'), output_vars, **cmd_kwargs
        )] + recipe_extra)

    deps = []
    if isinstance(rule, CompileHeader) and rule.pch_source:
        deps.append(rule.pch_source)
    deps.append(rule.file)
    if rule.pch:
        deps.append(rule.pch)
    deps.extend(rule.header_files)
    if compiler.needs_libs:
        deps.extend(rule.libs)

    dirs = uniques(i.path.parent() for i in rule.output)
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=deps + rule.extra_deps,
        order_only=[i.append(make.dir_sentinel) for i in dirs if i],
        recipe=make.Call(recipename, *output_params),
        variables=variables
    )


@ninja.rule_handler(CompileSource, CompileHeader)
def ninja_compile(rule, build_inputs, buildfile, env):
    compiler = rule.compiler
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)
    if rule.description:
        variables['description'] = rule.description

    if len(rule.output) == 1:
        output_vars = ninja.var('out')
    elif compiler.num_outputs == 1:
        output_vars = ninja.var('output')
        variables[output_vars] = rule.output[0]
    else:
        output_vars = []
        for i in range(compiler.num_outputs):
            v = ninja.var('output{}'.format(i + 1))
            output_vars.append(v)
            variables[v] = rule.output[i]

    if not buildfile.has_rule(compiler.rule_name):
        depfile = None
        deps = None

        if compiler.deps_flavor == 'gcc':
            deps = 'gcc'
            cmd_kwargs['deps'] = depfile = ninja.var('out') + '.d'
        elif compiler.deps_flavor == 'msvc':
            deps = 'msvc'
            cmd_kwargs['deps'] = True

        desc = rule.desc_verb + ' => ' + first(output_vars)
        buildfile.rule(name=compiler.rule_name, command=compiler(
            ninja.var('in'), output_vars, **cmd_kwargs
        ), depfile=depfile, deps=deps, description=desc)

    inputs = [rule.file]
    implicit_deps = []
    if rule.pch:
        implicit_deps.append(rule.pch)
    if isinstance(rule, CompileHeader) and rule.pch_source:
        inputs = [rule.pch_source]
        implicit_deps.append(rule.file)
    implicit_deps.extend(rule.header_files)
    if compiler.needs_libs:
        implicit_deps.extend(rule.libs)

    # Ninja doesn't support multiple outputs and deps-parsing at the same time,
    # so just use the first output and set up an alias if necessary. Aliases
    # aren't perfect, since the build can get out of sync if you delete the
    # "alias" file, but it's close enough.
    if compiler.deps_flavor in ('gcc', 'msvc') and len(rule.output) > 1:
        output = rule.output[0]
        buildfile.build(
            output=rule.output[1:],
            rule='phony',
            inputs=rule.output[0]
        )
    else:
        output = rule.output

    buildfile.build(
        output=output,
        rule=compiler.rule_name,
        inputs=inputs,
        implicit=implicit_deps + rule.extra_deps,
        variables=variables
    )


try:
    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(CompileSource, CompileHeader)
    def msbuild_compile(rule, build_inputs, solution, env):
        # MSBuild does compilation and linking in one unit; see link.py.
        pass
except ImportError:
    pass
