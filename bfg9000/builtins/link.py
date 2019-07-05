import os.path
import warnings
from collections import defaultdict
from itertools import chain
from six import string_types
from six.moves import filter as ifilter

from . import builtin
from .. import options as opts
from .file_types import local_file
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import (first, flatten, iterate, listify, merge_dicts,
                         merge_into_dict, slice_dict, uniques)
from ..shell import posix as pshell

build_input('link_options')(lambda build_inputs, env: {
    'dynamic': defaultdict(list), 'static': defaultdict(list)
})


class Link(Edge):
    msbuild_output = True
    extra_kwargs = ()

    def __init__(self, builtins, build, env, name, files=None, includes=None,
                 pch=None, libs=None, packages=None, compile_options=None,
                 link_options=None, entry_point=None, lang=None,
                 extra_deps=None, description=None):
        self.name = self.__name(name)

        self.user_libs = [
            builtins['library'](i, kind=self._preferred_lib, lang=lang)
            for i in iterate(libs)
        ]
        forward_opts = self.__get_forward_opts(self.user_libs)
        self.libs = self.user_libs + forward_opts.get('libs', [])

        self.user_packages = [builtins['package'](i)
                              for i in iterate(packages)]
        self.packages = self.user_packages + forward_opts.get('packages', [])

        self.user_files = builtins['object_files'](
            files, includes=includes, pch=pch, libs=self.user_libs,
            packages=self.user_packages, options=compile_options, lang=lang
        )
        self.files = self.user_files + flatten(
            getattr(i, 'extra_objects', []) for i in self.user_files
        )

        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.user_libs) ):
            raise ValueError('need at least one source file')

        self.user_options = pshell.listify(link_options, type=opts.option_list)

        if entry_point:
            self.entry_point = entry_point

        formats = uniques(i.format for i in chain(self.files, self.libs,
                                                  self.packages))
        if len(formats) > 1:
            raise ValueError('cannot link multiple object formats')

        self.langs = uniques(chain(
            (i.lang for i in self.files if i.lang is not None),
            (j for i in self.libs for j in iterate(i.lang))
        ))
        if not self.langs:
            raise ValueError('unable to determine language')

        self.linker = self.__find_linker(env, formats[0], self.langs)

        # Forward any necessary options to the compile step.
        if hasattr(self.linker, 'compile_options'):
            compile_opts = self.linker.compile_options(self)
        else:
            compile_opts = opts.option_list()
        compile_opts.extend(forward_opts.get('compile_options', []))
        for i in self.files:
            if hasattr(i.creator, 'add_extra_options'):
                i.creator.add_extra_options(compile_opts)

        extra_options = self.linker.pre_build(build, name, self)

        output = self.linker.output_file(name, self)
        primary = first(output)

        primary.package_deps.extend(self.packages)

        self._fill_options(env, extra_options, forward_opts, output)

        options = self.options
        public_output = self.linker.post_build(build, options, output, self)
        primary.post_install = self.linker.post_install(options, output, self)

        Edge.__init__(self, build, output, public_output, extra_deps,
                      description)

        build['defaults'].add(primary)

    @classmethod
    def __name(cls, name):
        head, tail = os.path.split(name)
        return os.path.join(head, cls._prefix + tail)

    @staticmethod
    def __get_forward_opts(libs):
        result = {}

        def accumulate(libs):
            for i in libs:
                if hasattr(i, 'forward_opts'):
                    merge_into_dict(result, i.forward_opts)
                    accumulate(i.forward_opts.get('libs', []))

        accumulate(libs)
        return result

    def __find_linker(self, env, format, langs):
        for i in langs:
            linker = env.builder(i).linker(self.mode)
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

    extra_kwargs = ('module_defs',)

    def __init__(self, builtins, *args, **kwargs):
        module_defs = kwargs.pop('module_defs', None)
        self.module_defs = (builtins['module_def_file'](module_defs)
                            if module_defs else None)
        Link.__init__(self, builtins, *args, **kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_options

    @property
    def flags(self):
        return self.linker.flags(self.options, self.raw_output)

    @property
    def lib_flags(self):
        return self.linker.lib_flags(self.options)

    def _fill_options(self, env, extra_options, forward_opts, output):
        linkers = (env.builder(i).linker(self.mode) for i in self.langs)
        self._internal_options = opts.option_list(
            opts.module_def(self.module_defs) if self.module_defs else None,
            (i.link_options(self.linker, output) for i in self.packages)
        )

        if self.linker.needs_libs:
            self._internal_options.collect(
                (i.always_libs(i is self.linker) for i in linkers),
                (opts.lib(i) for i in self.libs)
            )

        self._internal_options.extend(extra_options)
        self._internal_options.extend(forward_opts.get('link_options', []))

        first(output).runtime_deps.extend(
            i.runtime_file for i in self.libs if i.runtime_file
        )


class SharedLink(DynamicLink):
    desc_verb = 'shared-link'
    mode = 'shared_library'
    msbuild_mode = 'DynamicLibrary'
    _prefix = 'lib'

    extra_kwargs = DynamicLink.extra_kwargs + ('version', 'soversion')

    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', None)
        self.soversion = kwargs.pop('soversion', None)
        if (self.version is None) != (self.soversion is None):
            raise ValueError('specify both version and soversion or neither')
        DynamicLink.__init__(self, *args, **kwargs)


class StaticLink(Link):
    desc_verb = 'static-link'
    base_mode = 'static'
    mode = 'static_library'
    msbuild_mode = 'StaticLibrary'
    _preferred_lib = 'static'
    _prefix = 'lib'

    extra_kwargs = ('static_link_options',)

    def __init__(self, *args, **kwargs):
        self.user_static_options = pshell.listify(
            kwargs.pop('static_link_options', None),
            type=opts.option_list
        )
        Link.__init__(self, *args, **kwargs)

    @property
    def options(self):
        return self._internal_options + self.user_static_options

    @property
    def flags(self):
        # Only pass the static-link options to the static linker. The other
        # options are forwarded on to the dynamic linker when this library is
        # used.
        return self.linker.flags(self.options, self.raw_output)

    def _fill_options(self, env, extra_options, forward_opts, output):
        self._internal_options = extra_options

        primary = first(output)
        primary.forward_opts = {
            'compile_options': opts.option_list(),
            # Don't include libs in link_options, since later link steps will
            # handle adding them to their LDFLAGS.
            'link_options': self.user_options,
            'libs': self.libs,
            'packages': self.user_packages,
        }
        if hasattr(self.linker, 'forwarded_compile_options'):
            primary.forward_opts['compile_options'].extend(
                self.linker.forwarded_compile_options(self)
            )

        primary.linktime_deps.extend(self.user_libs)


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(Executable)
def executable(builtins, build, env, name, files=None, **kwargs):
    if files is None and 'libs' not in kwargs:
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        return local_file(build, Executable, name, params, kwargs)
    return DynamicLink(builtins, build, env, name, files,
                       **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(SharedLibrary, in_type=string_types + (DualUseLibrary,))
def shared_library(builtins, build, env, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.shared

    if files is None and 'libs' not in kwargs:
        # XXX: What to do for pre-built shared libraries for Windows, which has
        # a separate DLL file?
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        return local_file(build, SharedLibrary, name, params, kwargs)
    return SharedLink(builtins, build, env, name, files,
                      **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(StaticLibrary, in_type=string_types + (DualUseLibrary,))
def static_library(builtins, build, env, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.static

    if files is None and 'libs' not in kwargs:
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        return local_file(build, StaticLibrary, name, params, kwargs)
    return StaticLink(builtins, build, env, name, files,
                      **kwargs).public_output


@builtin.function('builtins', 'build_inputs', 'env')
@builtin.type(Library, in_type=string_types + (DualUseLibrary,))
def library(builtins, build, env, name, files=None, **kwargs):
    explicit_kind = False

    if 'kind' in kwargs:
        explicit_kind = True
        kind = kwargs.pop('kind')
    elif env.library_mode.shared and env.library_mode.static:
        kind = 'dual'
    elif env.library_mode.shared:
        kind = 'shared'
    elif env.library_mode.static:
        kind = 'static'
    else:
        raise ValueError('unable to create library: both shared and static ' +
                         'modes disabled')

    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name if kind == 'dual' else getattr(name, kind)

    if files is None and 'libs' not in kwargs:
        params = [('format', env.target_platform.object_format), ('lang', 'c')]
        file_type = StaticLibrary

        if explicit_kind:
            if kind == 'shared':
                file_type = SharedLibrary
                # Ignore the lang argument for shared libraries.
                params = params[:1]
                kwargs.pop('lang', None)
            elif kind == 'dual':
                raise ValueError("can't create dual-use libraries from an " +
                                 "existing file")

        # XXX: Try to detect if a string refers to a shared lib?
        return local_file(build, file_type, name, params, kwargs)

    shared_kwargs = slice_dict(kwargs, SharedLink.extra_kwargs)
    static_kwargs = slice_dict(kwargs, StaticLink.extra_kwargs)
    shared_kwargs.update(kwargs)
    static_kwargs.update(kwargs)

    if kind == 'dual':
        shared = SharedLink(builtins, build, env, name, files, **shared_kwargs)
        if not shared.linker.builder.can_dual_link:
            warnings.warn("dual linking not supported with {}"
                          .format(shared.linker.brand))
            return shared.public_output

        static = StaticLink(builtins, build, env, name, shared.files,
                            **static_kwargs)
        return DualUseLibrary(shared.public_output, static.public_output)
    elif kind == 'shared':
        return SharedLink(builtins, build, env, name, files,
                          **shared_kwargs).public_output
    else:  # kind == 'static'
        return StaticLink(builtins, build, env, name, files,
                          **static_kwargs).public_output


@builtin.function('builtins')
@builtin.type(WholeArchive, in_type=string_types + (StaticLibrary,))
def whole_archive(builtins, name, *args, **kwargs):
    if isinstance(name, StaticLibrary):
        if len(args) or len(kwargs):
            raise TypeError('unexpected arguments')
        return WholeArchive(name)
    else:
        return WholeArchive(builtins['static_library'](name, *args, **kwargs))


@builtin.function('build_inputs')
def global_link_options(build, options, family='native', mode='dynamic'):
    for i in iterate(family):
        build['link_options'][mode][i].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    variables = {}
    cmd_kwargs = {}

    linker = rule.linker
    if hasattr(linker, 'flags_var'):
        global_ldflags, ldflags = backend.flags_vars(
            linker.flags_var,
            (linker.global_flags +
             linker.flags(build_inputs['link_options'][rule.base_mode]
                          [linker.family])),
            buildfile
        )
        cmd_kwargs['flags'] = ldflags
        flags = rule.flags
        if flags:
            variables[ldflags] = [global_ldflags] + flags

    if hasattr(rule.linker, 'libs_var'):
        global_ldlibs, ldlibs = backend.flags_vars(
            rule.linker.libs_var, rule.linker.global_libs, buildfile
        )
        cmd_kwargs['libs'] = ldlibs
        lib_flags = rule.lib_flags
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
    if len(rule.output) == 1:
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
    if hasattr(rule.linker, 'transform_input'):
        files = rule.linker.transform_input(files)

    manifest = listify(getattr(rule, 'manifest', None))
    module_defs = listify(getattr(rule, 'module_defs', None))
    dirs = uniques(i.path.parent() for i in rule.output)
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=rule.files + rule.libs + module_defs + manifest + rule.extra_deps,
        order_only=[i.append(make.dir_sentinel) for i in dirs if i],
        recipe=make.Call(recipename, files, *output_params),
        variables=variables
    )


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink)
def ninja_link(rule, build_inputs, buildfile, env):
    linker = rule.linker
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)
    if rule.description:
        variables['description'] = rule.description

    if len(rule.output) == 1:
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

    if hasattr(rule.linker, 'transform_input'):
        input_var = ninja.var('input')
        variables[input_var] = rule.linker.transform_input(rule.files)
    else:
        input_var = ninja.var('in')

    if not buildfile.has_rule(linker.rule_name):
        buildfile.rule(name=linker.rule_name, command=linker(
            input_var, output_vars, **cmd_kwargs
        ), description=rule.desc_verb + ' => ' + first(output_vars))

    manifest = listify(getattr(rule, 'manifest', None))
    module_defs = listify(getattr(rule, 'module_defs', None))
    buildfile.build(
        output=rule.output,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=rule.libs + module_defs + manifest + rule.extra_deps,
        variables=variables
    )


try:
    from .compile import CompileHeader
    from ..backends.msbuild import writer as msbuild

    def _parse_compiler_cflags(compilers, global_options):
        per_compiler_cflags = {}
        for c in compilers:
            key = c.command_var
            if key not in per_compiler_cflags:
                per_compiler_cflags[key] = c.parse_flags(msbuild.textify_each(
                    c.global_flags + c.flags(global_options[c.lang])
                ))
        return per_compiler_cflags

    def _parse_file_cflags(file, per_compiler_cflags):
        cflags = file.creator.compiler.parse_flags(
            msbuild.textify_each(file.creator.flags)
        )
        if not per_compiler_cflags:
            return cflags
        key = file.creator.compiler.command_var
        return merge_dicts(per_compiler_cflags[key], cflags)

    @msbuild.rule_handler(DynamicLink, SharedLink, StaticLink)
    def msbuild_link(rule, build_inputs, solution, env):
        if ( any(i not in ['c', 'c++'] for i in rule.langs) or
             rule.linker.flavor != 'msvc' ):
            raise ValueError('msbuild backend currently only supports c/c++ ' +
                             'with msvc')

        output = rule.output[0]

        # Parse compilation flags; if there's only one set of them (i.e. the
        # command_var is the same for every compiler), we can apply these to
        # all the files at once. Otherwise, we need to apply them to each file
        # individually so they all get the correct options.
        obj_creators = [i.creator for i in rule.files]
        compilers = uniques(i.compiler for i in obj_creators)

        per_compiler_options = _parse_compiler_cflags(
            compilers, build_inputs['compile_options']
        )
        if len(per_compiler_options) == 1:
            common_compile_options = per_compiler_options.popitem()[1]
        else:
            common_compile_options = None

        # Parse linking flags.
        ldflags = [
            rule.linker.global_flags +
            rule.linker.flags(build_inputs['link_options'][rule.base_mode]
                              [rule.linker.family]) +
            rule.flags
        ]
        if hasattr(rule.linker, 'libs_var'):
            ldflags.append(rule.linker.global_libs + rule.lib_flags)
        link_options = rule.linker.parse_flags(
            *[msbuild.textify_each(i) for i in ldflags]
        )
        if hasattr(output, 'import_lib'):
            link_options['import_lib'] = output.import_lib

        deps = chain(
            (i.creator.file for i in rule.files),
            chain.from_iterable(i.creator.header_files for i in rule.files),
            chain.from_iterable(i.creator.extra_deps for i in rule.files),
            ifilter(None, (getattr(i.creator, 'pch_source', None)
                           for i in rule.files)),
            rule.libs, rule.extra_deps
        )

        def get_source(file):
            # Get the source file for this compilation rule; it's either a
            # regular source file or a PCH source file.
            if isinstance(file.creator, CompileHeader):
                return file.creator.pch_source
            return file.creator.file

        # Create the project file.
        project = msbuild.VcxProject(
            env, name=rule.name,
            mode=rule.msbuild_mode,
            output_file=output,
            files=[{
                'name': get_source(i),
                'options': _parse_file_cflags(i, per_compiler_options),
            } for i in rule.files],
            compile_options=common_compile_options,
            link_options=link_options,
            dependencies=solution.dependencies(deps),
        )
        solution[output] = project
except ImportError:
    pass
