import warnings
from collections import defaultdict
from six import string_types

from . import builtin
from .file_types import local_file
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import first, iterate, listify, uniques
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
    def __init__(self, builtins, build, env, name, includes=None, include=None,
                 pch=None, libs=None, packages=None, options=None, lang=None,
                 extra_deps=None):
        # XXX: Remove this after 0.3 is released.
        if include is not None:  # pragma: no cover
            warnings.warn("'include' keyword argument is deprecated; use " +
                          "'includes' instead")
            includes = include

        self.header_files = []
        self.includes = []
        for i in iterate(includes):
            if isinstance(i, HeaderFile):
                self.header_files.append(i)
            self.includes.append(builtins['header_directory'](i))

        # Don't bother handling forward_opts from libs now, since the only
        # languages that need libs during compilation don't support static
        # linking anyway.
        self.libs = [builtins['library'](i, lang=lang) for i in iterate(libs)]

        self.packages = [builtins['package'](i) for i in iterate(packages)]
        self.user_options = pshell.listify(options)

        if pch and not self.compiler.accepts_pch:
            raise TypeError('pch not supported for this compiler')
        self.pch = builtins['precompiled_header'](
            pch, file=pch, includes=includes, packages=self.packages,
            options=self.user_options, lang=lang
        ) if pch else None

        if hasattr(self.compiler, 'pre_build'):
            self.compiler.pre_build(build, self, name)

        output = self.compiler.output_file(name, self)
        public_output = None

        if hasattr(self.compiler, 'post_build'):
            public_output = self.compiler.post_build(build, self, output)

        self._internal_options = (
            self.compiler.flags(self, output) +
            sum((i.cflags(self.compiler, output) for i in self.packages), [])
        )

        Edge.__init__(self, build, output, public_output, extra_deps)

        if hasattr(self.compiler, 'post_install'):
            first(output).post_install = self.compiler.post_install(output)

    def add_link_options(self, *args, **kwargs):
        opts = self.compiler.link_flags(*args, **kwargs)
        self._internal_options.extend(opts)
        if self.pch and self.pch.creator:
            self.pch.creator.add_link_options(*args, **kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_options


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
        params = [('format', env.platform.object_format), ('lang', 'c')]
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
        build['compile_options'][i].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    variables = {}
    cmd_kwargs = {}

    if hasattr(rule.compiler, 'flags_var'):
        global_cflags, cflags = backend.flags_vars(
            rule.compiler.flags_var,
            ( rule.compiler.global_flags +
              build_inputs['compile_options'][rule.compiler.lang] ),
            buildfile
        )
        cmd_kwargs = {'flags': cflags}
        if rule.options:
            variables[cflags] = [global_cflags] + rule.options

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

            buildfile.include(rule.output[0].path.addext('.d'), optional=True)

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
    if compiler.depends_on_libs:
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

        buildfile.rule(name=compiler.rule_name, command=compiler(
            ninja.var('in'), output_vars, **cmd_kwargs
        ), depfile=depfile, deps=deps)

    inputs = [rule.file]
    implicit_deps = []
    if rule.pch:
        implicit_deps.append(rule.pch)
    if isinstance(rule, CompileHeader) and rule.pch_source:
        inputs = [rule.pch_source]
        implicit_deps.append(rule.file)
    implicit_deps.extend(rule.header_files)
    if compiler.depends_on_libs:
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
