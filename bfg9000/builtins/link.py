import os.path
import re
from itertools import chain
from six.moves import reduce

from .compile import ObjectFiles
from .hooks import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import first, iterate, listify, merge_dicts, uniques
from ..path import Path, Root
from ..shell import posix as pshell

build_input('link_options')(lambda build_inputs, env: list())

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


class Link(Edge):
    def __init__(self, builtins, build, env, name, files=None, include=None,
                 pch=None, libs=None, packages=None, compile_options=None,
                 link_options=None, entry_point=None, lang=None,
                 extra_deps=None):
        self.name = self.__name(name)

        # XXX: Try to detect if a string refers to a shared lib?
        self.user_libs = [objectify(
            i, Library, builtins['static_library'], lang=lang
        ) for i in iterate(libs)]
        fwd = [i.forward_args for i in self.user_libs
               if hasattr(i, 'forward_args')]
        self.libs = sum((i.get('libs', []) for i in fwd), self.user_libs)

        self.user_packages = [objectify(i, builtins['package'])
                              for i in iterate(packages)]
        self.packages = sum((i.get('packages', []) for i in fwd),
                            self.user_packages)

        self.user_files = objectify(
            files, builtins['object_files'],
            include=include, pch=pch, libs=self.user_libs,
            packages=self.user_packages, options=compile_options, lang=lang
        )
        self.files = sum(
            (getattr(i, 'extra_objects', []) for i in self.user_files),
            self.user_files
        )

        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.user_libs) ):
            raise ValueError('need at least one source file')

        if entry_point:
            self.entry_point = entry_point

        for c in (i.creator for i in self.files if i.creator):
            # To handle the different import/export rules for libraries, we
            # need to provide some LIBFOO_EXPORTS/LIBFOO_STATIC macros so the
            # build knows how to annotate public API functions in the headers.
            # XXX: One day, we could pass these as "semantic options" (i.e.
            # options that are specified like define('FOO') instead of
            # '-DFOO'). Then the linkers could generate those options in a more
            # generic way.
            macro = library_macro(self.name, self.mode)
            c.add_link_options(
                self.mode, sum((f.get('defines', []) for f in fwd), macro)
            )

        formats = uniques(i.format for i in chain(self.files, self.libs))
        if len(formats) > 1:
            raise ValueError('cannot link multiple object formats')

        self.langs = uniques(chain(
            (i.lang for i in self.files),
            chain.from_iterable(getattr(i, 'langs', []) for i in self.libs)
        ))
        self.linker = self.__find_linker(env, formats[0], self.langs)

        self.user_options = pshell.listify(link_options)
        self.forwarded_options = sum((i.get('options', []) for i in fwd), [])

        if hasattr(self.linker, 'pre_build'):
            self.linker.pre_build(build, self, name)

        output = self.linker.output_file(name, self)
        public_output = None

        if hasattr(self.linker, 'post_build'):
            public_output = self.linker.post_build(build, self, output)

        self._fill_options(env, output)

        Edge.__init__(self, build, output, public_output, extra_deps)

        primary = first(output)
        if hasattr(self.linker, 'post_install'):
            primary.post_install = self.linker.post_install(output)
        build['defaults'].add(primary)

    @classmethod
    def __name(cls, name):
        head, tail = os.path.split(name)
        return os.path.join(head, cls._prefix + tail)

    def __find_linker(self, env, format, langs):
        for i in langs:
            linker = env.builder(i).linker(self.mode)
            if linker.can_link(format, langs):
                return linker
        raise ValueError('unable to find linker')


class StaticLink(Link):
    mode = 'static_library'
    msbuild_mode = 'StaticLibrary'
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
            'defines': library_macro(self.name, self.mode),
            'options': self.forwarded_options + self.user_options,
            'libs': self.libs,
            'packages': self.packages,
        }
        primary.linktime_deps.extend(self.user_libs)


class DynamicLink(Link):
    mode = 'executable'
    msbuild_mode = 'Application'
    _prefix = ''

    @property
    def options(self):
        return (self._internal_options + self.forwarded_options +
                self.user_options)

    def _fill_options(self, env, output):
        self._internal_options = (
            sum((i.ldflags(self.linker, output)
                 for i in self.packages), []) +
            self.linker.args(self, output)
        )

        linkers = (env.builder(i).linker(self.mode) for i in self.langs)
        self.lib_options = (
            sum((i.always_libs(i is self.linker) for i in linkers), []) +
            sum((i.ldlibs(self.linker, output)
                 for i in self.packages), []) +
            self.linker.libs(self, output)
        )

        first(output).runtime_deps.extend(chain.from_iterable(
            self.__get_runtime_deps(i) for i in self.libs
        ))

    @staticmethod
    def __get_runtime_deps(lib):
        extra = []
        if isinstance(lib, SharedLibrary) and not isinstance(lib, LinkLibrary):
            extra = [lib]
        return lib.runtime_deps + extra


class SharedLink(DynamicLink):
    mode = 'shared_library'
    msbuild_mode = 'DynamicLibrary'
    _prefix = 'lib'

    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', None)
        self.soversion = kwargs.pop('soversion', None)
        if (self.version is None) != (self.soversion is None):
            raise ValueError('specify both version and soversion or neither')
        DynamicLink.__init__(self, *args, **kwargs)


def generic_link(builtins, build, env, file_type, edge_type, name, files=None,
                 **kwargs):
    if files is None and kwargs.get('libs') is None:
        object_format = kwargs.get('format', env.platform.object_format)
        return build.add_source(file_type(
            Path(name, Root.srcdir), object_format
        ))
    else:
        return edge_type(builtins, build, env, name, files,
                         **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(Executable)
def executable(builtins, build, env, *args, **kwargs):
    return generic_link(builtins, build, env, Executable, DynamicLink,
                        *args, **kwargs)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(StaticLibrary)
def static_library(builtins, build, env, *args, **kwargs):
    return generic_link(builtins, build, env, StaticLibrary, StaticLink,
                        *args, **kwargs)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(SharedLibrary)
def shared_library(builtins, build, env, *args, **kwargs):
    # XXX: What to do for pre-built shared libraries for Windows, which has a
    # separate DLL file?
    return generic_link(builtins, build, env, SharedLibrary, SharedLink,
                        *args, **kwargs)


@builtin.globals('builtins')
@builtin.type(WholeArchive)
def whole_archive(builtins, name, *args, **kwargs):
    if isinstance(name, StaticLibrary):
        if len(args) or len(kwargs):
            raise TypeError('unexpected arguments')
        return WholeArchive(name)
    else:
        return WholeArchive(builtins['static_library'](name, *args, **kwargs))


@builtin.globals('build_inputs')
def global_link_options(build, options):
    build['link_options'].extend(pshell.listify(options))


def _get_flags(backend, rule, build_inputs, buildfile):
    global_ldflags, ldflags = backend.flags_vars(
        rule.linker.flags_var,
        rule.linker.global_args + build_inputs['link_options'],
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
        buildfile.define(recipename, [
            linker(cmd=make.cmd_var(linker, buildfile), input=make.var('1'),
                   output=output_vars, **cmd_kwargs)
        ])

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


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink)
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
            cmd=ninja.cmd_var(linker, buildfile), input=input_var,
            output=output_vars, **cmd_kwargs
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

    @msbuild.rule_handler(StaticLink, DynamicLink, SharedLink)
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
            (rule.linker.global_args + build_inputs['link_options'] +
             rule.options)
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
