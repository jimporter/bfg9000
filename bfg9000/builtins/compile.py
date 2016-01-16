import os.path
from collections import defaultdict
from itertools import chain
from six import string_types

from . import builtin
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input, Edge
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..path import Path, Root
from ..shell import posix as pshell


build_input('compile_options')(lambda: defaultdict(list))


class ObjectFiles(list):
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
    def __init__(self, build, env, name, file, include=None,
                 packages=None, options=None, lang=None, extra_deps=None):
        if name is None:
            name = os.path.splitext(file)[0]

        self.file = sourcify(file, SourceFile, lang=lang)
        self.builder = env.compiler(self.file.lang)
        self.includes = [sourcify(i, HeaderDirectory)
                         for i in iterate(include)]
        self.packages = listify(packages)
        self.user_options = pshell.listify(options)
        self.link_options = []

        pkg_includes = chain.from_iterable(i.includes for i in self.packages)
        self.all_includes = uniques(chain(pkg_includes, self.includes))
        self._internal_options = sum(
            (self.builder.include_dir(i) for i in self.all_includes), []
        )

        target = self.builder.output_file(name)
        Edge.__init__(self, build, target, extra_deps)

    @property
    def options(self):
        return self._internal_options + self.link_options + self.user_options


@builtin.globals('build_inputs', 'env')
def object_file(build, env, name=None, file=None, **kwargs):
    if file is None:
        if name is None:
            raise TypeError('expected name')
        return ObjectFile(name, root=Root.srcdir, **kwargs)
    else:
        return Compile(build, env, name, file, **kwargs).target


@builtin.globals('build_inputs', 'env')
def object_files(build, env, files, **kwargs):
    def _compile(file, **kwargs):
        return Compile(build, env, None, file, **kwargs).target
    return ObjectFiles(objectify(i, ObjectFile, _compile, **kwargs)
                       for i in iterate(files))


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


@make.rule_handler(Compile)
def make_object_file(rule, build_inputs, buildfile, env):
    compiler = rule.builder
    variables, cmd_kwargs = _get_flags(make, rule, build_inputs, buildfile)

    recipename = make.var('RULE_{}'.format(compiler.rule_name.upper()))
    if not buildfile.has_variable(recipename):
        recipe_extra = []

        # Only GCC-style depfiles are supported by Make.
        if compiler.deps_flavor == 'gcc':
            depfixer = env.tool('depfixer')
            cmd_kwargs['deps'] = deps = make.qvar('@') + '.d'
            df_cmd = make.cmd_var(depfixer, buildfile)
            recipe_extra = [make.silent(depfixer(df_cmd, deps))]

        buildfile.define(recipename, [compiler(
            cmd=make.cmd_var(compiler, buildfile), input=make.qvar('<'),
            output=make.qvar('@'), **cmd_kwargs
        )] + recipe_extra)

    path = rule.target.path
    out_dir = path.parent()
    buildfile.rule(
        target=path,
        deps=[rule.file] + rule.extra_deps,
        order_only=[out_dir.append(make.dir_sentinel)] if out_dir else None,
        recipe=recipename,
        variables=variables
    )
    buildfile.include(path.addext('.d'), optional=True)


@ninja.rule_handler(Compile)
def ninja_object_file(rule, build_inputs, buildfile, env):
    compiler = rule.builder
    variables, cmd_kwargs = _get_flags(ninja, rule, build_inputs, buildfile)

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
            output=ninja.var('out'), **cmd_kwargs
        ), depfile=depfile, deps=deps)

    buildfile.build(
        output=rule.target,
        rule=compiler.rule_name,
        inputs=[rule.file],
        implicit=rule.extra_deps,
        variables=variables
    )
