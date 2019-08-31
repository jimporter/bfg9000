from collections import defaultdict
from six import string_types

from . import builtin
from .. import options as opts
from .file_types import static_file
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import first, iterate
from ..languages import known_langs
from ..path import Path, Root
from ..shell import posix as pshell

build_input('compile_options')(lambda build_inputs, env: defaultdict(list))


class FileList(list):
    def __init__(self, fn, files, **kwargs):
        list.__init__(self, (fn(i, **kwargs) for i in iterate(files)))

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


class BaseCompile(Edge):
    desc_verb = 'compile'

    def __init__(self, builtins, build, env, name, internal_options,
                 extra_deps=None, description=None):
        if name is None:
            name = self.compiler.default_name(self.file, self)

        extra_options = self.compiler.pre_build(build, name, self)
        output = self.compiler.output_file(name, self)
        primary = first(output)

        self._internal_options = opts.option_list(
            internal_options, extra_options
        )

        options = self.options
        public_output = self.compiler.post_build(build, options, output, self)
        primary.post_install = self.compiler.post_install(options, output,
                                                          self)

        Edge.__init__(self, build, output, public_output, extra_deps,
                      description)

    @property
    def options(self):
        return self._internal_options + self.user_options

    @property
    def flags(self):
        return self.compiler.flags(self.options, self.raw_output)


class Compile(BaseCompile):
    def __init__(self, builtins, build, env, name, includes=None, pch=None,
                 libs=None, packages=None, options=None, lang=None,
                 src_lang=None, extra_deps=None, description=None):
        self.packages = [builtins['package'](i, lang=src_lang)
                         for i in iterate(packages)]
        self.user_options = pshell.listify(options, type=opts.option_list)

        self.header_files = []
        self.includes = []
        for i in iterate(includes):
            if isinstance(i, SourceCodeFile):
                self.header_files.append(i)
            self.includes.append(builtins['header_directory'](i))

        internal_options = opts.option_list(
            (i.compile_options(self.compiler) for i in self.packages),
            (opts.include_dir(i) for i in self.includes)
        )

        self.pch = None
        if pch:
            if not self.compiler.accepts_pch:
                raise TypeError('pch not supported for this compiler')
            self.pch = builtins['precompiled_header'](
                pch, file=pch, includes=includes, packages=self.packages,
                options=self.user_options, lang=lang
            )
            internal_options.append(opts.pch(self.pch))

        # Don't bother handling forward_opts from libs now, since the only
        # languages that need libs during compilation don't support static
        # linking anyway.
        if self.compiler.needs_libs:
            self.libs = [builtins['library'](i, lang=src_lang)
                         for i in iterate(libs)]
            internal_options.extend(opts.lib(i) for i in self.libs)

        BaseCompile.__init__(self, builtins, build, env, name,
                             internal_options, extra_deps, description)

    def add_extra_options(self, options):
        self._internal_options.extend(options)
        # PCH files should always be built with the same options as files using
        # them, so forward the extra options onto the PCH if it exists.
        if self.pch and hasattr(self.pch.creator, 'add_extra_options'):
            self.pch.creator.add_extra_options(options)


class CompileSource(Compile):
    def __init__(self, builtins, build, env, name, file, lang=None, **kwargs):
        src_lang = known_langs[lang].src_lang if lang else None
        self.file = builtins['source_file'](file, lang=src_lang)
        if self.file.lang is None:
            raise ValueError('unable to determine language for file {!r}'
                             .format(self.file.path))

        self.compiler = env.builder(lang or self.file.lang).compiler
        Compile.__init__(self, builtins, build, env, name, lang=lang,
                         src_lang=src_lang, **kwargs)


class CompileHeader(Compile):
    desc_verb = 'compile-header'

    def __init__(self, builtins, build, env, name, file, lang=None, **kwargs):
        src_lang = known_langs[lang].src_lang if lang else None
        self.file = builtins['header_file'](file, lang=src_lang)
        if self.file.lang is None:
            raise ValueError('unable to determine language for file {!r}'
                             .format(self.file.path))

        source = kwargs.pop('source', None)
        self.pch_source = builtins['source_file'](
            source, lang=self.file.lang
        ) if source else None

        self.compiler = env.builder(lang or self.file.lang).pch_compiler
        Compile.__init__(self, builtins, build, env, name, lang=lang,
                         src_lang=src_lang, **kwargs)


class GenerateSource(BaseCompile):
    desc_verb = 'generate'

    def __init__(self, builtins, build, env, name, file, options=None,
                 lang=None, extra_deps=None, description=None):
        src_lang = known_langs[lang].src_lang if lang else None
        self.file = builtins['auto_file'](file, lang=src_lang)
        if not isinstance(self.file, CodeFile):
            raise ValueError('unable to determine language for file {!r}'
                             .format(self.file.path))

        self.user_options = pshell.listify(options, type=opts.option_list)

        self.compiler = env.builder(lang or self.file.lang).transpiler
        BaseCompile.__init__(self, builtins, build, env, name, None,
                             extra_deps, description)


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFile, extra_in_type=type(None))
def object_file(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        return static_file(build, ObjectFile, name, params, kwargs)
    return CompileSource(builtins, build, env, name, file,
                         **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(ObjectFile, extra_in_type=SourceFile)
def _make_object_file(builtins, build, env, file, **kwargs):
    return CompileSource(builtins, build, env, None, file,
                         **kwargs).public_output


@builtin.function('builtins')
@builtin.type(FileList, in_type=object)
def object_files(builtins, files, **kwargs):
    return FileList(builtins['_make_object_file'], files, **kwargs)


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(PrecompiledHeader, extra_in_type=type(None))
def precompiled_header(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        params = [('lang', 'c')]
        return static_file(build, PrecompiledHeader, name, params, kwargs)
    return CompileHeader(builtins, build, env, name, file,
                         **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(SourceCodeFile, extra_in_type=type(None))
def generated_source(builtins, build, env, name=None, file=None, **kwargs):
    if file is None:
        raise TypeError('expected file')
    return GenerateSource(builtins, build, env, name, file,
                          **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(SourceCodeFile, extra_in_type=CodeFile, short_circuit=False)
def _make_generated_source(builtins, build, env, file, **kwargs):
    return GenerateSource(builtins, build, env, None, file,
                          **kwargs).public_output


@builtin.function('builtins')
@builtin.type(FileList, in_type=object)
def generated_sources(builtins, files, **kwargs):
    return FileList(builtins['_make_generated_source'], files, **kwargs)


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


@make.rule_handler(CompileSource, CompileHeader, GenerateSource)
def make_compile(rule, build_inputs, buildfile, env):
    compiler = rule.compiler
    variables, cmd_kwargs = _get_flags(make, rule, build_inputs, buildfile)

    output_params = []
    if compiler.num_outputs == 'all':
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
    if getattr(rule, 'pch_source', None):
        deps.append(rule.pch_source)
    deps.append(rule.file)
    if getattr(rule, 'pch', None):
        deps.append(rule.pch)
    deps.extend(getattr(rule, 'header_files', []))
    if compiler.needs_libs:
        deps.extend(rule.libs)

    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=deps + rule.extra_deps,
        order_only=make.directory_deps(rule.output),
        recipe=make.Call(recipename, *output_params),
        variables=variables
    )


@ninja.rule_handler(CompileSource, CompileHeader, GenerateSource)
def ninja_compile(rule, build_inputs, buildfile, env):
    compiler = rule.compiler
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)
    if rule.description:
        variables['description'] = rule.description

    if compiler.num_outputs == 'all':
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
    if getattr(rule, 'pch', None):
        implicit_deps.append(rule.pch)
    if getattr(rule, 'pch_source', None):
        inputs = [rule.pch_source]
        implicit_deps.append(rule.file)
    implicit_deps.extend(getattr(rule, 'header_files', []))
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
