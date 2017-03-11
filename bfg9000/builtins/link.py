import os.path
import re
from collections import defaultdict
from itertools import chain
from six import string_types
from six.moves import reduce

from . import builtin
from .compile import Compile, ObjectFiles
from .file_types import local_file
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import (first, iterate, listify, merge_dicts, merge_into_dict,
                         uniques)
from ..path import Path, Root
from ..shell import posix as pshell

build_input('link_options')(lambda build_inputs, env: defaultdict(list))

_modes = {
    'shared_library': 'EXPORTS',
    'static_library': 'STATIC',
}


def library_macro(name, mode):
    if mode not in _modes:
        return []

    # Since the name always begins with "lib", this always produces a valid
    # macro name.
    return ['{name}_{suffix}'.format(
        name=re.sub(r'\W', '_', name.upper()), suffix=_modes[mode]
    )]


def library_version(kwargs):
    version = kwargs.pop('version', None)
    soversion = kwargs.pop('soversion', None)
    if (version is None) != (soversion is None):
        raise ValueError('specify both version and soversion or neither')
    return version, soversion


class Link(Edge):
    def __init__(self, builtins, build, env, name, files=None, includes=None,
                 include=None, pch=None, libs=None, packages=None,
                 compile_options=None, link_options=None, entry_point=None,
                 lang=None, extra_deps=None):
        self.name = self.__name(name)

        self.user_libs = [
            builtins['library'](i, kind=self._preferred_lib, lang=lang)
            for i in iterate(libs)
        ]
        forward_args = self.__get_forward_args(self.user_libs)
        self.libs = self.user_libs + forward_args.get('libs', [])

        self.user_packages = [builtins['package'](i)
                              for i in iterate(packages)]
        self.packages = self.user_packages + forward_args.get('packages', [])

        # XXX: Remove `include` after 0.3 is released.
        self.user_files = builtins['object_files'](
            files, includes=includes, include=include, pch=pch,
            libs=self.user_libs, packages=self.user_packages,
            options=compile_options, lang=lang
        )
        self.files = sum(
            (getattr(i, 'extra_objects', []) for i in self.user_files),
            self.user_files
        )

        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.user_libs) ):
            raise ValueError('need at least one source file')

        self.user_options = pshell.listify(link_options)
        self.forwarded_options = forward_args.get('options', [])

        if entry_point:
            self.entry_point = entry_point

        formats = uniques(i.format for i in chain(self.files, self.libs,
                                                  self.packages))
        if len(formats) > 1:
            raise ValueError('cannot link multiple object formats')

        self.langs = uniques(chain(
            (i.lang for i in self.files),
            (j for i in self.libs for j in iterate(i.lang))
        ))
        self.linker = self.__find_linker(env, formats[0], self.langs)

        # To handle the different import/export rules for libraries, we need to
        # provide some LIBFOO_EXPORTS/LIBFOO_STATIC macros so the build knows
        # how to annotate public API functions in the headers. XXX: One day, we
        # could pass these as "semantic options" (i.e. options that are
        # specified like define('FOO') instead of '-DFOO'). Then the linkers
        # could generate those options in a more generic way.
        defines = []
        if self.linker.has_link_macros:
            defines = library_macro(self.name, self.mode)
        defines = forward_args.get('defines', []) + defines

        for i in self.files:
            if isinstance(i.creator, Compile):
                i.creator.add_link_options(self.mode, defines)

        if hasattr(self.linker, 'pre_build'):
            self.linker.pre_build(build, self, name)

        output = self.linker.output_file(name, self)
        primary = first(output)
        public_output = None

        if hasattr(self.linker, 'post_build'):
            public_output = self.linker.post_build(build, self, output)

        self._fill_options(env, output)

        Edge.__init__(self, build, output, public_output, extra_deps)

        if hasattr(self.linker, 'post_install'):
            primary.post_install = self.linker.post_install(output)
        build['defaults'].add(primary)

    @classmethod
    def __name(cls, name):
        head, tail = os.path.split(name)
        return os.path.join(head, cls._prefix + tail)

    @staticmethod
    def __get_forward_args(libs):
        result = {}

        def accumulate(libs):
            for i in libs:
                if hasattr(i, 'forward_args'):
                    merge_into_dict(result, i.forward_args)
                    accumulate(i.forward_args.get('libs', []))

        accumulate(libs)
        return result

    def __find_linker(self, env, format, langs):
        for i in langs:
            linker = env.builder(i).linker(self.mode)
            if linker.can_link(format, langs):
                return linker
        raise ValueError('unable to find linker')


class DynamicLink(Link):
    mode = 'executable'
    msbuild_mode = 'Application'
    _preferred_lib = 'shared'
    _prefix = ''

    @property
    def options(self):
        return (self._internal_options + self.forwarded_options +
                self.user_options)

    def _fill_options(self, env, output):
        if hasattr(self.linker, 'args'):
            self._internal_options = (
                sum((i.ldflags(self.linker, output)
                     for i in self.packages), []) +
                self.linker.args(self, output)
            )
        else:
            self._internal_options = []

        if hasattr(self.linker, 'libs'):
            linkers = (env.builder(i).linker(self.mode) for i in self.langs)
            self.lib_options = (
                sum((i.always_libs(i is self.linker) for i in linkers), []) +
                sum((i.ldlibs(self.linker, output)
                     for i in self.packages), []) +
                self.linker.libs(self, output)
            )

        first(output).runtime_deps.extend(
            i.runtime_file for i in self.libs if i.runtime_file
        )


class SharedLink(DynamicLink):
    mode = 'shared_library'
    msbuild_mode = 'DynamicLibrary'
    _prefix = 'lib'

    def __init__(self, *args, **kwargs):
        self.version, self.soversion = library_version(kwargs)
        DynamicLink.__init__(self, *args, **kwargs)


class StaticLink(Link):
    mode = 'static_library'
    msbuild_mode = 'StaticLibrary'
    _preferred_lib = 'static'
    _prefix = 'lib'

    @property
    def options(self):
        # Don't pass any options to the static linker. XXX: We used to support
        # this for users via `link_options`, but that's used for forwarding
        # options to a dynamic linker now. Should we add support for static
        # link options back in under a different name?
        return []

    def _fill_options(self, env, output):
        primary = first(output)
        primary.forward_args = {
            'options': self.user_options,
            'libs': self.user_libs,
            'packages': self.user_packages,
        }
        if self.linker.has_link_macros:
            macro = library_macro(self.name, self.mode)
            primary.forward_args['defines'] = macro

        primary.linktime_deps.extend(self.user_libs)


class DualedStaticLink(StaticLink):
    def __init__(self, *args, **kwargs):
        library_version(kwargs)
        StaticLink.__init__(self, *args, **kwargs)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(Executable)
def executable(builtins, build, env, name, files=None, **kwargs):
    if files is None and 'libs' not in kwargs:
        params = [('format', env.platform.object_format), ('lang', 'c')]
        return local_file(build, Executable, name, params, **kwargs)
    return DynamicLink(builtins, build, env, name, files,
                       **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(SharedLibrary, in_type=(string_types, DualUseLibrary))
def shared_library(builtins, build, env, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.shared

    if files is None and 'libs' not in kwargs:
        # XXX: What to do for pre-built shared libraries for Windows, which has
        # a separate DLL file?
        params = [('format', env.platform.object_format), ('lang', 'c')]
        return local_file(build, SharedLibrary, name, params, **kwargs)
    return SharedLink(builtins, build, env, name, files,
                      **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(StaticLibrary, in_type=(string_types, DualUseLibrary))
def static_library(builtins, build, env, name, files=None, **kwargs):
    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name.static

    if files is None and 'libs' not in kwargs:
        params = [('format', env.platform.object_format), ('lang', 'c')]
        return local_file(build, StaticLibrary, name, params, **kwargs)
    return StaticLink(builtins, build, env, name, files,
                      **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(Library, in_type=(string_types, DualUseLibrary))
def library(builtins, build, env, name, files=None, **kwargs):
    if env.library_mode.shared and env.library_mode.static:
        kind = 'dual'
    elif env.library_mode.shared:
        kind = 'shared'
    elif env.library_mode.static:
        kind = 'static'
    else:
        raise ValueError('unable to create library: both shared and static ' +
                         'modes disabled')

    explicit_kind = 'kind' in kwargs
    kind = kwargs.pop('kind', kind)

    if isinstance(name, DualUseLibrary):
        if files is not None or not set(kwargs.keys()) <= {'format', 'lang'}:
            raise TypeError('unexpected arguments')
        return name if kind == 'dual' else getattr(name, kind)

    if files is None and 'libs' not in kwargs:
        params = [('format', env.platform.object_format), ('lang', 'c')]
        file_type = StaticLibrary

        if explicit_kind:
            if kind == 'shared':
                file_type = SharedLibrary
                # Ignore the lang argument for shared libraries.
                params = params[:1]
                kwargs.pop('lang')
            elif kind == 'dual':
                raise ValueError("can't create dual-use libraries from an " +
                                 "existing file")

        # XXX: Try to detect if a string refers to a shared lib?
        return local_file(build, file_type, name, params, **kwargs)

    if kind in ['dual']:
        shared = SharedLink(builtins, build, env, name, files, **kwargs)
        if not env.builder(shared.linker.lang).can_dual_link:
            return shared.public_output

        static = DualedStaticLink(builtins, build, env, name, shared.files,
                                  **kwargs)
        return DualUseLibrary(shared.public_output, static.public_output)
    elif kind == 'shared':
        return SharedLink(builtins, build, env, name, files,
                          **kwargs).public_output
    else:  # kind == 'static'
        return DualedStaticLink(builtins, build, env, name, files,
                                **kwargs).public_output


@builtin.globals('builtins')
@builtin.type(WholeArchive, in_type=(string_types, StaticLibrary))
def whole_archive(builtins, name, *args, **kwargs):
    if isinstance(name, StaticLibrary):
        if len(args) or len(kwargs):
            raise TypeError('unexpected arguments')
        return WholeArchive(name)
    else:
        return WholeArchive(builtins['static_library'](name, *args, **kwargs))


@builtin.globals('build_inputs')
def global_link_options(build, options, family='native'):
    for i in iterate(family):
        build['link_options'][i].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    global_ldflags, ldflags = backend.flags_vars(
        rule.linker.flags_var,
        ( rule.linker.global_args +
          build_inputs['link_options'][rule.linker.family] ),
        buildfile
    )

    variables = {}
    cmd_kwargs = {'args': ldflags}

    if rule.options:
        variables[ldflags] = [global_ldflags] + rule.options

    if hasattr(rule, 'lib_options'):
        global_ldlibs, ldlibs = backend.flags_vars(
            rule.linker.libs_var, rule.linker.global_libs, buildfile
        )
        cmd_kwargs['libs'] = ldlibs
        if rule.lib_options:
            variables[ldlibs] = [global_ldlibs] + rule.lib_options

    if hasattr(rule, 'manifest'):
        var = backend.var('manifest')
        cmd_kwargs['manifest'] = var
        variables[var] = rule.manifest

    return variables, cmd_kwargs


@make.rule_handler(StaticLink, DynamicLink, SharedLink, DualedStaticLink)
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
    dirs = uniques(i.path.parent() for i in rule.output)
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=rule.files + rule.libs + manifest + rule.extra_deps,
        order_only=[i.append(make.dir_sentinel) for i in dirs if i],
        recipe=make.Call(recipename, files, *output_params),
        variables=variables
    )


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink, DualedStaticLink)
def ninja_link(rule, build_inputs, buildfile, env):
    linker = rule.linker
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)

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
        buildfile.rule(name=linker.rule_name, command=[linker(
            input_var, output_vars, **cmd_kwargs
        )])

    manifest = listify(getattr(rule, 'manifest', None))
    buildfile.build(
        output=rule.output,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=rule.libs + manifest + rule.extra_deps,
        variables=variables
    )


try:
    from .compile import CompileHeader
    from ..backends.msbuild import writer as msbuild

    def _reduce_compile_options(files, global_cflags):
        creators = [i.creator for i in files if i.creator]
        compilers = uniques(i.linker for i in creators)

        return reduce(merge_dicts, chain(
            (i.parse_args(msbuild.textify_each(
                i.global_args + global_cflags[i.lang]
            )) for i in compilers),
            (i.linker.parse_args(msbuild.textify_each(
                i.options
            )) for i in creators)
        ))

    def _parse_common_cflags(compiler, global_cflags):
        return compiler.parse_args(msbuild.textify_each(
            compiler.global_args + global_cflags[compiler.lang]
        ))

    def _parse_file_cflags(file, per_compiler_cflags):
        cflags = file.creator.compiler.parse_args(
            msbuild.textify_each(file.creator.options)
        )
        if not per_compiler_cflags:
            return cflags
        key = file.creator.compiler.command_var
        return merge_dicts(per_compiler_cflags[key], cflags)

    @msbuild.rule_handler(DynamicLink, SharedLink, StaticLink,
                          DualedStaticLink)
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

        per_compiler_cflags = {}
        for c in compilers:
            key = c.command_var
            if key not in per_compiler_cflags:
                per_compiler_cflags[key] = c.parse_args(msbuild.textify_each(
                    c.global_args + build_inputs['compile_options'][c.lang]
                ))

        if len(per_compiler_cflags) == 1:
            common_cflags = per_compiler_cflags.popitem()[1]
        else:
            common_cflags = None

        # Parse linking flags.
        ldflags = rule.linker.parse_args(msbuild.textify_each(
            (rule.linker.global_args +
             build_inputs['link_options'][rule.linker.family] + rule.options)
        ))
        ldflags['libs'] = (
            getattr(rule.linker, 'global_libs', []) +
            getattr(rule, 'lib_options', [])
        )
        if hasattr(output, 'import_lib'):
            ldflags['import_lib'] = output.import_lib

        deps = chain(
            (i.creator.file for i in rule.files),
            chain.from_iterable(i.creator.header_files for i in rule.files),
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

        # Create the project file.
        project = msbuild.VcxProject(
            env, name=rule.name,
            mode=rule.msbuild_mode,
            output_file=output,
            files=[{
                'name': get_source(i),
                'options': _parse_file_cflags(i, per_compiler_cflags),
            } for i in rule.files],
            compile_options=common_cflags,
            link_options=ldflags,
            dependencies=solution.dependencies(deps),
        )
        solution[output] = project
except:
    pass
