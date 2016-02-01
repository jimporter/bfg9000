import os.path
from itertools import chain

from .hooks import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..path import Root
from ..shell import posix as pshell


build_input('link_options')(list)


class Link(Edge):
    @classmethod
    def __name(cls, name):
        head, tail = os.path.split(name)
        return os.path.join(head, cls._prefix + tail)

    def __init__(self, builtins, build, env, name, files, include=None,
                 libs=None, packages=None, compile_options=None,
                 link_options=None, lang=None, extra_deps=None):
        self.name = self.__name(name)
        self.packages = listify(packages)

        # XXX: Try to detect if a string refers to a shared lib?
        self.libs = [sourcify(i, Library, StaticLibrary)
                     for i in iterate(libs)]
        self.all_libs = sum((i.libraries for i in self.packages), self.libs)

        self.files = builtins['object_files'](
            files, include=include, packages=packages, options=compile_options,
            lang=lang
        )
        if ( len(self.files) == 0 and
             not any(isinstance(i, WholeArchive) for i in self.libs) ):
            raise ValueError('need at least one source file')

        langs = chain([lang], (i.lang for i in self.files),
                      (i.lang for i in self.all_libs))
        self.builder = env.linker(langs, self.mode)

        self.user_options = pshell.listify(link_options)
        self._internal_options = []

        target = self.builder.output_file(name)
        target.runtime_deps = [ i for i in self.libs
                                if isinstance(i, SharedLibrary) ]
        if hasattr(self.builder, 'post_install'):
            target.post_install = self.builder.post_install

        for c in (i.creator for i in self.files if i.creator):
            c.link_options.extend(c.builder.link_args(self.name, self.mode))

        build['defaults'].add(target)
        Edge.__init__(self, build, target, extra_deps)

    @property
    def options(self):
        return self._internal_options + self.user_options


class StaticLink(Link):
    mode = 'static_library'
    msbuild_mode = 'StaticLibrary'
    _prefix = 'lib'

    def __init__(self, *args, **kwargs):
        Link.__init__(self, *args, **kwargs)
        if self.options:
            raise ValueError('link options are not allowed for static ' +
                             'libraries')
        if self.all_libs:
            raise ValueError('libraries cannot be linked into static ' +
                             'libraries')


class DynamicLink(Link):
    mode = 'executable'
    msbuild_mode = 'Application'
    _prefix = ''

    def __init__(self, *args, **kwargs):
        Link.__init__(self, *args, **kwargs)
        links = sum((self.builder.link_lib(i) for i in self.all_libs), [])
        self.lib_options = links

        dirs = sum((i.lib_dirs for i in self.packages), self.all_libs)
        lib_dirs = self.builder.lib_dirs(dirs, self.target)
        self._internal_options.extend(lib_dirs)


class SharedLink(DynamicLink):
    mode = 'shared_library'
    msbuild_mode = 'DynamicLibrary'
    _prefix = 'lib'

    def __init__(self, *args, **kwargs):
        DynamicLink.__init__(self, *args, **kwargs)
        self._internal_options.extend(self.builder.import_lib(self.target))


@builtin.globals('builtins', 'build_inputs', 'env')
def executable(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        return Executable(name, root=Root.srcdir, **kwargs)
    else:
        return DynamicLink(builtins, build, env, name, files, **kwargs).target


@builtin.globals('builtins', 'build_inputs', 'env')
def static_library(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        return StaticLibrary(name, root=Root.srcdir, **kwargs)
    else:
        return StaticLink(builtins, build, env, name, files, **kwargs).target


@builtin.globals('builtins', 'build_inputs', 'env')
def shared_library(builtins, build, env, name, files=None, **kwargs):
    if files is None and kwargs.get('libs') is None:
        # XXX: What to do here for Windows, which has a separate DLL file?
        return SharedLibrary(name, root=Root.srcdir, **kwargs)
    else:
        return SharedLink(builtins, build, env, name, files, **kwargs).target


@builtin
def whole_archive(lib):
    lib = sourcify(lib, StaticLibrary)
    return WholeArchive(lib)


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

    ldflags_value = rule.builder.mode_args + rule.options
    if ldflags_value:
        variables[ldflags] = [global_ldflags] + ldflags_value

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

    recipename = make.var('RULE_{}'.format(linker.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [
            linker(cmd=make.cmd_var(linker, buildfile), input=make.var('1'),
                   output=make.var('2'), **cmd_kwargs)
        ])

    recipe = make.Call(recipename, rule.files, rule.target.path)
    if len(rule.target.all) > 1:
        target = rule.target.path.addext('.stamp')
        buildfile.rule(target=rule.target.all, deps=[target])
        recipe = [recipe, make.silent([ 'touch', make.var('@') ])]
    else:
        target = rule.target

    dirs = uniques(i.path.parent() for i in rule.target.all)
    buildfile.rule(
        target=target,
        deps=rule.files + rule.libs + rule.extra_deps,
        order_only=[i.append(make.dir_sentinel) for i in dirs if i],
        recipe=recipe,
        variables=variables
    )


@ninja.rule_handler(StaticLink, DynamicLink, SharedLink)
def ninja_link(rule, build_inputs, buildfile, env):
    linker = rule.builder
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)
    variables[ninja.var('output')] = rule.target.path

    if not buildfile.has_rule(linker.rule_name):
        buildfile.rule(name=linker.rule_name, command=linker(
            cmd=ninja.cmd_var(linker, buildfile), input=ninja.var('in'),
            output=ninja.var('output'), **cmd_kwargs
        ))

    buildfile.build(
        output=rule.target.all,
        rule=linker.rule_name,
        inputs=rule.files,
        implicit=rule.libs + rule.extra_deps,
        variables=variables
    )

try:
    from ..backends.msbuild import writer as msbuild

    def _reduce_options(files, global_options):
        compilers = uniques(i.creator.builder for i in files)
        langs = uniques(i.lang for i in files)

        per_file_opts = []
        for i in files:
            # We intentionally exclude internal_options, since MSBuild handles
            # these its own way.
            for opts in [i.creator.link_options, i.creator.user_options]:
                if opts not in per_file_opts:
                    per_file_opts.append(opts)

        return list(chain(
            chain.from_iterable(i.global_args for i in compilers),
            chain.from_iterable(global_options[i] for i in langs),
            chain.from_iterable(per_file_opts)
        ))

    @msbuild.rule_handler(StaticLink, DynamicLink, SharedLink)
    def msbuild_link(rule, build_inputs, solution, env):
        # By definition, a dependency for an edge must already be defined by
        # the time the edge is created, so we can map *all* the dependencies to
        # their associated projects by looking at the projects we've already
        # created.
        dependencies = []
        for dep in rule.libs:
            if dep.creator.target not in solution:
                raise ValueError('unknown dependency for {!r}'.format(dep))
            dependencies.append(solution[dep.creator.target])

        includes = uniques(chain.from_iterable(
            i.creator.all_includes for i in rule.files
        ))

        project = msbuild.VcxProject(
            name=rule.name,
            version=env.getvar('VISUALSTUDIOVERSION'),
            mode=rule.msbuild_mode,
            platform=env.getvar('PLATFORM'),
            output_file=rule.target,
            srcdir=env.srcdir.string(),
            files=[i.creator.file for i in rule.files],
            compile_options=_reduce_options(
                rule.files, build_inputs['compile_options']
            ),
            includes=includes,
            # We intentionally exclude internal_options from the link step,
            # since MSBuild handles these its own way.
            link_options=(
                rule.user_options + rule.builder.global_args +
                build_inputs['link_options']
            ),
            libs=rule.all_libs,
            lib_dirs=sum((i.lib_dirs for i in rule.packages), []),
            dependencies=dependencies,
        )
        solution[rule.target] = project
except:
    pass
