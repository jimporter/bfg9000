import os.path
import warnings
from collections import defaultdict
from itertools import chain

from . import builtin
from .. import options as opts
from .file_types import static_file
from .path import relname
from ..backends.compdb import writer as compdb
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..exceptions import ToolNotFoundError
from ..file_types import *
from ..iterutils import (first, flatten, iterate, listify, slice_dict, uniques,
                         unlistify)
from ..languages import known_formats
from ..objutils import convert_each, convert_one
from ..platforms import known_native_object_formats
from ..shell import posix as pshell

build_input('link_options')(lambda build_inputs, env: {
    'dynamic': defaultdict(list), 'static': defaultdict(list)
})


class Link(Edge):
    msbuild_output = True
    extra_kwargs = ()

    def __init__(self, context, name, files, libs, packages, link_options,
                 lang=None, extra_deps=None, description=None):
        build = context.build
        name = relname(context, name)
        self.name = self.__name(name)

        self.user_libs = libs
        forward_opts = opts.ForwardOptions.recurse(self.user_libs)
        self.libs = self.user_libs + forward_opts.libs

        self.user_packages = packages
        self.packages = self.user_packages + forward_opts.packages

        self.user_files = files
        self.files = self.user_files + flatten(
            getattr(i, 'extra_objects', []) for i in self.user_files
        )

        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.user_libs) ):
            raise ValueError('need at least one source file')

        self.user_options = link_options

        formats = uniques(i.format for i in chain(self.files, self.libs,
                                                  self.packages))
        if len(formats) > 1:
            raise ValueError('cannot link multiple object formats')
        self.format = formats[0]

        self.input_langs = uniques(chain(
            (i.lang for i in self.files if i.lang is not None),
            (j for i in self.libs for j in iterate(i.lang))
        ))
        if not lang and not self.input_langs:
            raise ValueError('unable to determine language')

        self.langs = [lang] if lang else self.input_langs
        self.linker = self.__find_linker(context.env, formats[0], self.langs)

        # Forward any necessary options to the compile step.
        if hasattr(self.linker, 'compile_options'):
            compile_opts = self.linker.compile_options(self)
        else:
            compile_opts = opts.option_list()
        compile_opts.extend(forward_opts.compile_options)
        for i in self.files:
            if hasattr(i.creator, 'add_extra_options'):
                i.creator.add_extra_options(compile_opts)

        extra_options = self.linker.pre_output(context, name, self)
        self._fill_options(context.env, extra_options, forward_opts)

        output = self.linker.output_file(name, self)
        primary = first(output)

        primary.package_deps.extend(self.packages)
        self._fill_output(output)

        options = self.options
        public_output = self.linker.post_output(context, options, output, self)
        primary.post_install = self.linker.post_install(options, output, self)

        super().__init__(build, output, public_output, extra_deps, description)
        build['defaults'].add(self.public_output)

    @classmethod
    def convert_args(cls, context, name, files, kwargs):
        lang = kwargs.get('lang')

        convert_each(kwargs, 'libs', context['library'],
                     kind=cls._preferred_lib, lang=lang)
        convert_each(kwargs, 'packages', context['package'], lang=lang)

        kwargs['link_options'] = pshell.listify(kwargs.get('link_options'),
                                                type=opts.option_list)

        intdir = ('{}.int/'.format(cls.__name(name))
                  if context.build['project']['intermediate_dirs'] else None)
        intdir = kwargs.pop('intermediate_dir', intdir)

        files = context['object_files'](
            files, includes=kwargs.pop('includes', None),
            pch=kwargs.pop('pch', None),
            options=kwargs.pop('compile_options', None),
            libs=kwargs['libs'], packages=kwargs['packages'], lang=lang,
            directory=intdir,
            extra_deps=kwargs.pop('extra_compile_deps', None)
        )

        return files, kwargs

    def _get_linkers(self, env, langs):
        yielded = False
        for i in langs:
            try:
                linker = env.builder(i).linker(self.mode)
                if linker:
                    yielded = True
                    yield linker
            except ToolNotFoundError:
                pass
        if not yielded:
            fmt = ('native' if self.format in known_native_object_formats
                   else self.format)
            src_lang = known_formats[fmt].src_lang
            yield env.builder(src_lang).linker(self.mode)

    @classmethod
    def __name(cls, name):
        head, tail = os.path.split(name)
        return os.path.join(head, cls._prefix + tail)

    def __find_linker(self, env, format, langs):
        for linker in self._get_linkers(env, langs):
            if linker.can_link(format, langs):
                return linker
        raise ValueError('unable to find linker')


class DynamicLink(Link):
    desc_verb = 'link'
    base_mode = 'dynamic'
    mode = 'executable'
    msbuild_mode = 'Application'
    _preferred_lib = 'shared'
    _prefix = ''

    extra_kwargs = ('entry_point', 'module_defs')

    def __init__(self, *args, entry_point=None, module_defs=None, **kwargs):
        self.entry_point = entry_point
        self.module_defs = module_defs
        super().__init__(*args, **kwargs)

    @classmethod
    def convert_args(cls, context, name, files, kwargs):
        convert_one(kwargs, 'module_defs', context['module_def_file'])
        return super().convert_args(context, name, files, kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_options

    def flags(self, global_options=None):
        return self.linker.flags(self.options, global_options, self.raw_output)

    def lib_flags(self, global_options=None):
        return self.linker.lib_flags(self.options, global_options)

    def _fill_options(self, env, extra_options, forward_opts):
        self._internal_options = opts.option_list(
            opts.entry_point(self.entry_point) if self.entry_point else None,
            opts.module_def(self.module_defs) if self.module_defs else None
        )

        if self.linker.needs_libs:
            linkers = self._get_linkers(env, self.input_langs)
            self._internal_options.collect(
                (i.always_libs(i is self.linker) for i in linkers),
                (opts.lib(i) for i in self.libs)
            )

        if self.linker.needs_package_options:
            self._internal_options.collect(i.link_options(self.linker)
                                           for i in self.packages)

        self._internal_options.collect(extra_options,
                                       forward_opts.link_options)

    def _fill_output(self, output):
        first(output).runtime_deps.extend(
            i.runtime_file for i in self.libs if i.runtime_file
        )


class SharedLink(DynamicLink):
    desc_verb = 'shared-link'
    mode = 'shared_library'
    msbuild_mode = 'DynamicLibrary'
    _prefix = 'lib'

    extra_kwargs = DynamicLink.extra_kwargs + ('version', 'soversion')

    def __init__(self, *args, version=None, soversion=None, **kwargs):
        self.version = version
        self.soversion = soversion
        if (self.version is None) != (self.soversion is None):
            raise ValueError('specify both version and soversion or neither')
        super().__init__(*args, **kwargs)


class StaticLink(Link):
    desc_verb = 'static-link'
    base_mode = 'static'
    mode = 'static_library'
    msbuild_mode = 'StaticLibrary'
    _preferred_lib = 'static'
    _prefix = 'lib'

    extra_kwargs = ('static_link_options',)

    def __init__(self, *args, static_link_options=None, **kwargs):
        self.user_static_options = static_link_options
        super().__init__(*args, **kwargs)

    @classmethod
    def convert_args(cls, context, name, files, kwargs):
        kwargs['static_link_options'] = pshell.listify(
            kwargs.get('static_link_options'), type=opts.option_list
        )
        return super().convert_args(context, name, files, kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_static_options

    def flags(self, global_options=None):
        # Only pass the static-link options to the static linker. The other
        # options are forwarded on to the dynamic linker when this library is
        # used.
        return self.linker.flags(self.options, global_options, self.raw_output)

    def _fill_options(self, env, extra_options, forward_opts):
        self._internal_options = extra_options

    def _fill_output(self, output):
        primary = first(output)
        primary.forward_opts = opts.ForwardOptions(
            link_options=self.user_options,
            libs=self.user_libs,
            packages=self.user_packages,
        )
        if hasattr(self.linker, 'forwarded_compile_options'):
            primary.forward_opts.compile_options.extend(
                self.linker.forwarded_compile_options(self)
            )

        primary.linktime_deps.extend(self.user_libs)


@builtin.function()
@builtin.type(Executable)
def executable(context, name, files=None, **kwargs):
    if files is None and 'libs' not in kwargs:
        dist = kwargs.pop('dist', True)
        params = [('format', context.env.target_platform.object_format),
                  ('lang', context.build['project']['lang'])]
        return static_file(context, Executable, name, dist, params, kwargs)
    files, kwargs = DynamicLink.convert_args(context, name, files, kwargs)
    return DynamicLink(context, name, files, **kwargs).public_output


@builtin.function()
@builtin.type(SharedLibrary, extra_in_type=DualUseLibrary)
def shared_library(context, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.shared

    if files is None and 'libs' not in kwargs:
        # XXX: What to do for pre-built shared libraries for Windows, which has
        # a separate DLL file?
        dist = kwargs.pop('dist', True)
        params = [('format', context.env.target_platform.object_format),
                  ('lang', context.build['project']['lang'])]
        return static_file(context, SharedLibrary, name, dist, params, kwargs)
    files, kwargs = SharedLink.convert_args(context, name, files, kwargs)
    return SharedLink(context, name, files, **kwargs).public_output


@builtin.function()
@builtin.type(StaticLibrary, extra_in_type=DualUseLibrary)
def static_library(context, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.static

    if files is None and 'libs' not in kwargs:
        dist = kwargs.pop('dist', True)
        params = [('format', context.env.target_platform.object_format),
                  ('lang', context.build['project']['lang'])]
        return static_file(context, StaticLibrary, name, dist, params, kwargs)
    files, kwargs = StaticLink.convert_args(context, name, files, kwargs)
    return StaticLink(context, name, files, **kwargs).public_output


@builtin.function()
@builtin.type(Library, extra_in_type=DualUseLibrary)
def library(context, name, files=None, *, kind=None, **kwargs):
    explicit_kind = False

    if kind is not None:
        explicit_kind = True
    elif context.env.library_mode.shared and context.env.library_mode.static:
        kind = 'dual'
    elif context.env.library_mode.shared:
        kind = 'shared'
    elif context.env.library_mode.static:
        kind = 'static'

    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name if kind == 'dual' else getattr(name, kind)

    if files is None and 'libs' not in kwargs:
        dist = kwargs.pop('dist', True)
        params = [('format', context.env.target_platform.object_format),
                  ('lang', context.build['project']['lang'])]
        file_type = StaticLibrary

        if explicit_kind:
            if kind == 'shared':
                file_type = SharedLibrary
            elif kind == 'dual':
                raise ValueError(
                    "can't create dual-use libraries from an existing file"
                )

        # XXX: Try to detect if a string refers to a shared lib?
        return static_file(context, file_type, name, dist, params, kwargs)

    if kind is None:
        raise ValueError('unable to create library: both shared and static ' +
                         'modes disabled')

    shared_kwargs = slice_dict(kwargs, SharedLink.extra_kwargs)
    static_kwargs = slice_dict(kwargs, StaticLink.extra_kwargs)
    shared_kwargs.update(kwargs)
    static_kwargs.update(kwargs)

    if kind == 'dual':
        shared_files, shared_kwargs = SharedLink.convert_args(
            context, name, files, shared_kwargs
        )
        shared = SharedLink(context, name, shared_files, **shared_kwargs)
        if not shared.linker.builder.can_dual_link:
            warnings.warn('dual linking not supported with {}'
                          .format(shared.linker.brand))
            return shared.public_output

        static_files, static_kwargs = StaticLink.convert_args(
            context, name, shared_files, static_kwargs
        )
        static = StaticLink(context, name, static_files, **static_kwargs)
        return DualUseLibrary(shared.public_output, static.public_output)
    elif kind == 'shared':
        files, kw = SharedLink.convert_args(context, name, files,
                                            shared_kwargs)
        return SharedLink(context, name, files, **kw).public_output
    else:  # kind == 'static'
        files, kw = StaticLink.convert_args(context, name, files,
                                            static_kwargs)
        return StaticLink(context, name, files, **kw).public_output


@builtin.function()
@builtin.type(WholeArchive, extra_in_type=StaticLibrary)
def whole_archive(context, name, *args, **kwargs):
    if isinstance(name, StaticLibrary):
        if len(args) or len(kwargs):
            raise TypeError('unexpected arguments')
        return WholeArchive(name)
    else:
        return WholeArchive(context['static_library'](name, *args, **kwargs))


@builtin.function()
def global_link_options(context, options, family='native', mode='dynamic'):
    for i in iterate(family):
        context.build['link_options'][mode][i].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    variables = {}
    cmd_kwargs = {}

    linker = rule.linker
    if hasattr(linker, 'flags_var') or hasattr(linker, 'libs_var'):
        gopts = build_inputs['link_options'][rule.base_mode][linker.family]

    if hasattr(linker, 'flags_var'):
        global_ldflags, ldflags = backend.flags_vars(
            linker.flags_var,
            linker.global_flags + linker.flags(gopts, mode='global'),
            buildfile
        )
        cmd_kwargs['flags'] = ldflags
        flags = rule.flags(gopts)
        if flags:
            variables[ldflags] = [global_ldflags] + flags

    if hasattr(linker, 'libs_var'):
        global_ldlibs, ldlibs = backend.flags_vars(
            linker.libs_var,
            linker.global_libs + linker.lib_flags(gopts, mode='global'),
            buildfile
        )
        cmd_kwargs['libs'] = ldlibs
        lib_flags = rule.lib_flags(gopts)
        if lib_flags:
            variables[ldlibs] = [global_ldlibs] + lib_flags

    if hasattr(rule, 'manifest'):
        var = backend.var('manifest')
        cmd_kwargs['manifest'] = var
        variables[var] = rule.manifest

    return variables, cmd_kwargs


@make.rule_handler(StaticLink, DynamicLink, SharedLink)
def make_link(rule, build_inputs, buildfile, env):
    linker = rule.linker
    variables, cmd_kwargs = _get_flags(make, rule, build_inputs, buildfile)

    output_params = []
    if linker.num_outputs == 'all':
        output_vars = make.qvar('@')
    else:
        output_vars = []
        for i in range(linker.num_outputs):
            v = make.var(str(i + 2))
            output_vars.append(v)
            output_params.append(rule.output[i])

    recipename = make.var('RULE_{}'.format(linker.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [linker(
            make.var('1'), output_vars, **cmd_kwargs
        )])

    files = rule.files
    if hasattr(linker, 'transform_input'):
        files = linker.transform_input(files)

    package_build_deps = flatten(i.deps for i in rule.packages)
    module_defs = listify(getattr(rule, 'module_defs', None))
    manifest = listify(getattr(rule, 'manifest', None))
    make.multitarget_rule(
        build_inputs, buildfile,
        targets=rule.output,
        deps=(rule.files + rule.libs + package_build_deps + module_defs +
              manifest + rule.extra_deps),
        order_only=make.directory_deps(rule.output),
        recipe=make.Call(recipename, files, *output_params),
        variables=variables
    )


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink)
def ninja_link(rule, build_inputs, buildfile, env):
    linker = rule.linker
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)
    if rule.description:
        variables['description'] = rule.description

    if linker.num_outputs == 'all':
        output_vars = ninja.var('out')
    elif linker.num_outputs == 1:
        output_vars = ninja.var('output')
        variables[output_vars] = rule.output[0]
    else:
        output_vars = []
        for i in range(linker.num_outputs):
            v = ninja.var('output{}'.format(i + 1))
            output_vars.append(v)
            variables[v] = rule.output[i]

    if hasattr(linker, 'transform_input'):
        input_var = ninja.var('input')
        variables[input_var] = linker.transform_input(rule.files)
    else:
        input_var = ninja.var('in')

    if not buildfile.has_rule(linker.rule_name):
        buildfile.rule(name=linker.rule_name, command=linker(
            input_var, output_vars, **cmd_kwargs
        ), description=rule.desc_verb + ' => ' + first(output_vars))

    package_build_deps = flatten(i.deps for i in rule.packages)
    module_defs = listify(getattr(rule, 'module_defs', None))
    manifest = listify(getattr(rule, 'manifest', None))
    buildfile.build(
        output=rule.output,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=(rule.libs + package_build_deps + module_defs + manifest +
                  rule.extra_deps),
        variables=variables
    )


@compdb.rule_handler(StaticLink, DynamicLink, SharedLink)
def compdb_link(rule, build_inputs, buildfile, env):
    linker = rule.linker
    cmd_kwargs = {}

    if hasattr(linker, 'flags_var') or hasattr(linker, 'libs_var'):
        gopts = build_inputs['link_options'][rule.base_mode][linker.family]
    if hasattr(linker, 'flags_var'):
        cmd_kwargs['flags'] = (linker.global_flags +
                               linker.flags(gopts, mode='global') +
                               rule.flags(gopts))
    if hasattr(linker, 'libs_var'):
        cmd_kwargs['libs'] = (linker.global_libs +
                              linker.lib_flags(gopts, mode='global') +
                              rule.lib_flags(gopts))
    if hasattr(rule, 'manifest'):
        cmd_kwargs['manifest'] = rule.manifest

    file = rule.files[0] if len(rule.files) else rule.user_libs[0]
    in_files = rule.files
    if hasattr(linker, 'transform_input'):
        in_files = linker.transform_input(in_files)
    output = unlistify(rule.output if linker.num_outputs == 'all'
                       else rule.output[0:linker.num_outputs])
    buildfile.append(
        arguments=linker(in_files, output, **cmd_kwargs),
        file=file, output=first(rule.public_output)
    )


try:
    from .compile import CompileHeader
    from ..backends.msbuild import writer as msbuild

    def _parse_compiler_cflags(compiler, global_options):
        return compiler.parse_flags(msbuild.textify_each(
            compiler.global_flags +
            compiler.flags(global_options[compiler.lang], mode='global')
        ))

    def _parse_file_cflags(file, global_options, include_compiler=False):
        compiler = file.creator.compiler
        gopts = global_options[compiler.lang]
        cflags = file.creator.flags(gopts)
        if include_compiler:
            cflags = (compiler.global_flags +
                      compiler.flags(gopts, mode='global') +
                      cflags)

        return compiler.parse_flags(msbuild.textify_each(cflags))

    def _parse_ldflags(rule, global_options):
        linker = rule.linker
        gopts = global_options[rule.base_mode][linker.family]
        primary = first(rule.output)

        ldflags = [linker.global_flags + linker.flags(gopts) +
                   rule.flags(gopts)]
        if hasattr(rule.linker, 'libs_var'):
            ldflags.append(linker.global_libs + linker.lib_flags(gopts) +
                           rule.lib_flags(gopts))

        link_options = linker.parse_flags(
            *[msbuild.textify_each(i) for i in ldflags]
        )
        if hasattr(primary, 'import_lib'):
            link_options['import_lib'] = primary.import_lib

        return link_options

    @msbuild.rule_handler(DynamicLink, SharedLink, StaticLink)
    def msbuild_link(rule, build_inputs, solution, env):
        if ( any(i not in ['c', 'c++', 'rc'] for i in rule.input_langs) or
             rule.linker.flavor != 'msvc' ):
            raise ValueError('msbuild backend currently only supports c/c++ ' +
                             'with msvc')

        global_compile_opts = build_inputs['compile_options']
        global_link_opts = build_inputs['link_options']

        # Parse compilation flags; if there's only one set of them (i.e. the
        # command_var is the same for every compiler), we can apply these to
        # all the files at once. Otherwise, we need to apply them to each file
        # individually so they all get the correct options.
        obj_creators = [i.creator for i in rule.files]
        compilers = uniques(i.compiler for i in obj_creators)

        if len(uniques(i.command_var for i in compilers)) == 1:
            common_compile_options = _parse_compiler_cflags(
                compilers[0], global_compile_opts
            )
        else:
            common_compile_options = None

        deps = chain(
            (i.creator.file for i in rule.files),
            chain.from_iterable(i.creator.include_deps for i in rule.files),
            chain.from_iterable(i.creator.extra_deps for i in rule.files),
            filter(None, (getattr(i.creator, 'pch_source', None)
                          for i in rule.files)),
            rule.libs, rule.extra_deps
        )

        def get_source(file):
            # Get the source file for this compilation rule; it's either a
            # regular source file or a PCH source file.
            if isinstance(file.creator, CompileHeader):
                return file.creator.pch_source
            return file.creator.file

        # MSBuild doesn't build anything if it thinks there are no object files
        # to link. This is a problem for building libraries with no sources
        # that link to a whole-archive (a fairly-common way of making a shared
        # library out of a static one). To get around this, explicitly add the
        # whole-archive as an object file to link, in addition to passing
        # `/WHOLEARCHIVE:foo` as usual.
        objs = []
        if not rule.files:
            for i in rule.libs:
                if isinstance(i, WholeArchive):
                    objs.append(i.library)

        # Create the project file.
        project = msbuild.VcxProject(
            env, name=rule.name,
            mode=rule.msbuild_mode,
            output_file=first(rule.output),
            files=[{
                'name': get_source(i),
                'options': _parse_file_cflags(
                    i, global_compile_opts,
                    include_compiler=(common_compile_options is None)
                ),
            } for i in rule.files],
            objs=objs,
            compile_options=common_compile_options,
            link_options=_parse_ldflags(rule, global_link_opts),
            dependencies=solution.dependencies(deps),
        )
        solution[first(rule.public_output)] = project
except ImportError:  # pragma: no cover
    pass
