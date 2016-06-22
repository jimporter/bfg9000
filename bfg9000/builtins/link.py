import os.path
from itertools import chain
from six.moves import reduce

from .compile import ObjectFiles
from .hooks import builtin
from .symlink import Symlink
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import first, iterate, listify, merge_dicts, uniques
from ..path import Root
from ..shell import posix as pshell

build_input('link_options')(lambda build_inputs, env: list())


class Link(Edge):
    def __init__(self, builtins, build, env, name, files=None, include=None,
                 pch=None, libs=None, packages=None, compile_options=None,
                 link_options=None, lang=None, extra_deps=None):
        self.name = self.__name(name)

        self.files = objectify(
            files, ObjectFiles, builtins['object_files'], object,
            include=include, pch=pch, packages=packages,
            options=compile_options, lang=lang
        )
        self.files.extend(chain.from_iterable(
            getattr(i, 'extra_objects', []) for i in self.files
        ))

        # XXX: Try to detect if a string refers to a shared lib?
        self.libs = [objectify(
            i, Library, builtins['static_library'], lang=lang
        ) for i in iterate(libs)]
        fwd = [i.forward_args for i in self.libs if hasattr(i, 'forward_args')]
        self.all_libs = sum((i.get('libs', []) for i in fwd), self.libs)

        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.libs) ):
            raise ValueError('need at least one source file')

        self.packages = listify(packages)
        self.all_packages = sum((i.get('packages', []) for i in fwd),
                                self.packages)

        for c in (i.creator for i in self.files if i.creator):
            # XXX: Passing all the static libs' names to the compiler to add
            # the appropriate macros is a bit convoluted. Perhaps this could be
            # simplified when we add support for "semantic options" (i.e.
            # options that are specified like define('FOO') instead of
            # '-DFOO'). Then the linkers could generate those options in a
            # generic way.
            c.add_link_options(self.name, self.mode,
                               (f['name'] for f in fwd if 'name' in f))

        formats = uniques(chain( (i.format for i in self.files),
                                 (i.format for i in self.all_libs) ))
        if len(formats) > 1:
            raise ValueError('cannot link multiple object formats')

        self.langs = uniques(chain(
            (i.lang for i in self.files),
            chain.from_iterable(getattr(i, 'lang', []) for i in self.all_libs)
        ))
        self.builder = self.__find_linker(env, formats[0], self.langs)

        self.user_options = pshell.listify(link_options)
        self._extra_options = sum((i.get('link_options', []) for i in fwd), [])
        self._internal_options = []

        output = self._output_file(name)
        Edge.__init__(self, build, output, extra_deps)

        self._fill_options(env)

        primary = first(output)
        if hasattr(self.builder, 'post_install'):
            primary.post_install = self.builder.post_install(output)
        build['defaults'].add(primary)

    @property
    def options(self):
        return self._internal_options + self._extra_options + self.user_options

    def _output_file(self, name):
        return self.builder.output_file(name)

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

    def _fill_options(self, env):
        primary = first(self.output)
        primary.forward_args = {
            'name': self.name,
            'options': self.options,
            'libs': self.libs,
            'packages': self.packages,
        }

    def _output_file(self, name):
        langs = uniques(i.lang for i in self.files)
        return self.builder.output_file(name, langs)


class DynamicLink(Link):
    mode = 'executable'
    msbuild_mode = 'Application'
    _prefix = ''

    def _fill_options(self, env):
        # XXX: Create a LinkOptions namedtuple for managing these args?
        self._internal_options = (
            sum((i.ldflags(self.builder, self.output)
                 for i in self.all_packages), []) +
            self.builder.args(self.all_libs, self.output)
        )

        linkers = (env.builder(i).linker(self.mode) for i in self.langs)
        self.lib_options = (
            sum((i.always_libs(i is self.builder) for i in linkers), []) +
            sum((i.ldlibs(self.builder, self.output)
                 for i in self.all_packages), []) +
            self.builder.libs(self.all_libs)
        )

        first(self.output).runtime_deps = sum(
            (self.__get_runtime_deps(i) for i in self.libs), []
        )

    @staticmethod
    def __get_runtime_deps(library):
        if isinstance(library, LinkLibrary):
            return library.runtime_deps
        elif isinstance(library, SharedLibrary):
            return [library]
        else:
            return []


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

    def _output_file(self, name):
        return self.builder.output_file(name, self.version, self.soversion)


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(Executable)
def executable(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        object_format = kwargs.get('format', env.platform.object_format)
        return build.add_source(Executable(
            Path(name, Root.srcdir), object_format
        ))
    else:
        return DynamicLink(builtins, build, env, name, files,
                           **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(StaticLibrary)
def static_library(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        object_format = kwargs.get('format', env.platform.object_format)
        lang = kwargs.get('lang', 'c')
        return build.add_source(StaticLibrary(
            Path(name, Root.srcdir), object_format, lang
        ))
    else:
        return StaticLink(builtins, build, env, name, files,
                          **kwargs).public_output


@builtin.globals('builtins', 'build_inputs', 'env')
@builtin.type(SharedLibrary)
def shared_library(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        # XXX: What to do here for Windows, which has a separate DLL file?
        object_format = kwargs.get('format', env.platform.object_format)
        return build.add_source(SharedLibrary(
            Path(name, Root.srcdir), object_format
        ))
    else:
        output = SharedLink(builtins, build, env, name, files,
                            **kwargs).public_output
        if not isinstance(output, VersionedSharedLibrary):
            return output

        # Make symlinks for the various versions of the shared lib.
        Symlink(build, output.soname, output)
        Symlink(build, output.link, output.soname)
        return output.link


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
        rule.builder.link_var + 'flags',
        rule.builder.global_args + build_inputs['link_options'],
        buildfile
    )

    variables = {}
    cmd_kwargs = {'args': ldflags}

    if rule.options:
        variables[ldflags] = [global_ldflags] + rule.options

    if hasattr(rule, 'lib_options'):
        global_ldlibs, ldlibs = backend.flags_vars(
            rule.builder.link_var + 'libs', rule.builder.global_libs, buildfile
        )
        cmd_kwargs['libs'] = ldlibs
        if rule.lib_options:
            variables[ldlibs] = [global_ldlibs] + rule.lib_options

    return variables, cmd_kwargs


@make.rule_handler(StaticLink, DynamicLink, SharedLink)
def make_link(rule, build_inputs, buildfile, env):
    linker = rule.builder
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

    dirs = uniques(i.path.parent() for i in rule.output)
    make.multitarget_rule(
        buildfile,
        targets=rule.output,
        deps=rule.files + rule.libs + rule.extra_deps,
        order_only=[i.append(make.dir_sentinel) for i in dirs if i],
        recipe=make.Call(recipename, rule.files, *output_params),
        variables=variables
    )


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink)
def ninja_link(rule, build_inputs, buildfile, env):
    linker = rule.builder
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

    if not buildfile.has_rule(linker.rule_name):
        buildfile.rule(name=linker.rule_name, command=linker(
            cmd=ninja.cmd_var(linker, buildfile), input=ninja.var('in'),
            output=output_vars, **cmd_kwargs
        ))

    buildfile.build(
        output=rule.output,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=rule.libs + rule.extra_deps,
        variables=variables
    )

try:
    from ..backends.msbuild import writer as msbuild

    def _reduce_compile_options(files, global_cflags):
        creators = [i.creator for i in files if i.creator]
        compilers = uniques(i.builder for i in creators)

        return reduce(merge_dicts, chain(
            (i.parse_args(msbuild.textify_each(
                i.global_args + global_cflags[i.lang]
            )) for i in compilers),
            (i.builder.parse_args(msbuild.textify_each(
                i.options
            )) for i in creators)
        ))

    def _parse_common_cflags(compiler, global_cflags):
        return compiler.parse_args(msbuild.textify_each(
            compiler.global_args + global_cflags[compiler.lang]
        ))

    def _parse_file_cflags(file, per_compiler_cflags):
        cflags = file.creator.builder.parse_args(
            msbuild.textify_each(file.creator.options)
        )
        if not per_compiler_cflags:
            return cflags
        key = file.creator.builder.command_var
        return merge_dicts(per_compiler_cflags[key], cflags)

    @msbuild.rule_handler(StaticLink, DynamicLink, SharedLink)
    def msbuild_link(rule, build_inputs, solution, env):
        output = rule.output[0]

        # Parse compilation flags; if there's only one set of them (i.e. the
        # command_var is the same for every compiler), we can apply these to
        # all the files at once. Otherwise, we need to apply them to each file
        # individually so they all get the correct options.
        obj_creators = [i.creator for i in rule.files]
        compilers = uniques(i.builder for i in obj_creators)

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
        ldflags = rule.builder.parse_args(msbuild.textify_each(
            (rule.builder.global_args + build_inputs['link_options'] +
             rule.options)
        ))
        ldflags['libs'] = (
            getattr(rule.builder, 'global_libs', []) +
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

        # Create the project file.
        project = msbuild.VcxProject(
            env, name=rule.name,
            mode=rule.msbuild_mode,
            output_file=output,
            files=[{
                'name': getattr(i.creator, 'pch_source', i.creator.file),
                'options': _parse_file_cflags(i, per_compiler_cflags),
            } for i in rule.files],
            compile_options=common_cflags,
            link_options=ldflags,
            dependencies=solution.dependencies(deps),
        )
        solution[output] = project
except:
    pass
