import functools
from collections import defaultdict
from six import string_types

from .echo_file import EchoFile
from .hooks import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..languages import lang2src
from ..path import Path, Root
from ..shell import posix as pshell

build_input('compile_options')(lambda build_inputs, env: defaultdict(list))


class ObjectFiles(list):
    def __init__(self, builtins, build, env, files, **kwargs):
        bound = functools.partial(builtins['object_file'], None)
        list.__init__(self, (objectify(
            i, ObjectFile, bound, in_type=(string_types, SourceFile), **kwargs
        ) for i in iterate(files)))

    def __getitem__(self, key):
        if isinstance(key, string_types):
            key = Path(key, Root.srcdir)
        elif isinstance(key, File):
            key = key.path

        if isinstance(key, Path):
            for i in self:
                if i.creator and i.creator.file.path == key:
                    return i
            raise ValueError("{!r} not found".format(key))
        else:
            return list.__getitem__(self, key)


class Compile(Edge):
    def __init__(self, builtins, build, env, output, include, pch, packages,
                 options, lang, extra_deps, extra_args=[]):
        self.header_files = []
        self.includes = []
        for i in iterate(include):
            if isinstance(i, HeaderFile):
                self.header_files.append(i)

            self.includes.append(objectify(
                i, HeaderDirectory, builtins['header_directory'],
                in_type=(string_types, HeaderFile), system=False
            ))

        self.packages = listify(packages)
        self.user_options = pshell.listify(options)

        self.pch = objectify(
            pch, PrecompiledHeader, builtins['precompiled_header'],
            build=build, env=env, file=pch, include=include,
            packages=self.packages, options=self.user_options, lang=lang
        ) if pch else None
        if self.pch and isinstance(self.pch, MsvcPrecompiledHeader):
            output.extra_objects = [self.pch.object_file]

        self._internal_options = (
            self.builder.args(self.includes, self.pch, *extra_args) +
            sum((i.cflags(self.builder, output) for i in self.packages), [])
        )

        Edge.__init__(self, build, output, extra_deps)

    def add_link_options(self, *args, **kwargs):
        opts = self.builder.link_args(*args, **kwargs)
        self._internal_options.extend(opts)
        if self.pch and self.pch.creator:
            self.pch.creator.add_link_options(*args, **kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_options


class CompileSource(Compile):
    def __init__(self, builtins, build, env, name, file, include=None,
                 pch=None, packages=None, options=None, lang=None,
                 extra_deps=None):
        self.file = objectify(file, SourceFile, builtins['source_file'],
                              lang=lang)
        if name is None:
            name = self.file.path.stripext().suffix

        self.builder = env.builder(self.file.lang).compiler
        output = self.builder.output_file(name)
        Compile.__init__(self, builtins, build, env, output, include, pch,
                         packages, options, lang, extra_deps)


class CompileHeader(Compile):
    def __init__(self, builtins, build, env, name, file, source=None,
                 include=None, pch=None, packages=None, options=None,
                 lang=None, extra_deps=None):
        self.file = objectify(file, HeaderFile, builtins['header_file'],
                              lang=lang)
        if name is None:
            name = self.file.path.suffix

        self.builder = env.builder(self.file.lang).pch_compiler

        extra_options = []
        extra_args = []
        if self.builder.needs_source:
            if source is None:
                ext = lang2src[self.file.lang][0]
                source = SourceFile(self.file.path.stripext(ext),
                                    self.file.lang)
                source.path.root = Root.builddir

                text = '#include "{}"'.format(self.file.path.basename())
                EchoFile(build, source, text)
                extra_options = self.builder.args([
                    Directory(self.file.path.parent(), None)
                ])
            else:
                source = objectify(source, SourceFile, builtins['source_file'],
                                   lang=self.file.lang)

            extra_args.append(self.file)
            self.pch_source = source
            source_name = self.pch_source.path.stripext().suffix
            output = self.builder.output_file(name, source_name)
        else:
            output = self.builder.output_file(name)

        Compile.__init__(self, builtins, build, env, output, include, None,
                         packages, options, lang, extra_deps, extra_args)
        self._internal_options.extend(extra_options)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFile)
def object_file(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        object_format = kwargs.get('format', env.platform.object_format)
        lang = kwargs.get('lang', 'c')
        return build.add_source(ObjectFile(
            Path(name, Root.srcdir), object_format, lang
        ))
    else:
        return CompileSource(builtins, build, env, name, file,
                             **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
def object_files(builtins, build, env, files, **kwargs):
    return ObjectFiles(builtins, build, env, files, **kwargs)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(PrecompiledHeader)
def precompiled_header(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        lang = kwargs.get('lang', 'c')
        return build.add_source(PrecompiledHeader(
            Path(name, Root.srcdir), lang
        ))
    else:
        return CompileHeader(builtins, build, env, name, file,
                             **kwargs).public_output


@builtin.globals('build_inputs')
def global_options(build, options, lang):
    build['compile_options'][lang].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    global_cflags, cflags = backend.flags_vars(
        rule.builder.command_var + 'flags',
        ( rule.builder.global_args +
          build_inputs['compile_options'][rule.file.lang] ),
        buildfile
    )

    variables = {}

    cflags_value = rule.options
    if cflags_value:
        variables[cflags] = [global_cflags] + cflags_value

    return variables, {'args': cflags}


@make.rule_handler(CompileSource, CompileHeader)
def make_compile(rule, build_inputs, buildfile, env):
    compiler = rule.builder
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
            cmd_kwargs['deps'] = deps = make.qvar('@') + '.d'
            df_cmd = make.cmd_var(depfixer, buildfile)
            recipe_extra = [make.silent(depfixer(df_cmd, deps))]

            buildfile.include(rule.output[0].path.addext('.d'), optional=True)

        buildfile.define(recipename, [compiler(
            cmd=make.cmd_var(compiler, buildfile), input=make.qvar('<'),
            output=output_vars, **cmd_kwargs
        )] + recipe_extra)

    deps = []
    if hasattr(rule, 'pch_source'):
        deps.append(rule.pch_source)
    deps.append(rule.file)
    if rule.pch:
        deps.append(rule.pch)
    deps.extend(rule.header_files)

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
    compiler = rule.builder
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
            cmd=ninja.cmd_var(compiler, buildfile), input=ninja.var('in'),
            output=output_vars, **cmd_kwargs
        ), depfile=depfile, deps=deps)

    inputs = [rule.file]
    implicit_deps = []
    if rule.pch:
        implicit_deps.append(rule.pch)
    if hasattr(rule, 'pch_source'):
        inputs = [rule.pch_source]
        implicit_deps.append(rule.file)
    implicit_deps.extend(rule.header_files)

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
except:
    pass
