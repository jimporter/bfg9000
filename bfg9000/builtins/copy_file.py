import os

from . import builtin
from .file_types import FileList, make_file_list, static_file
from .path import buildpath, relname, within_directory
from ..backends.compdb import writer as compdb
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import Edge
from ..file_types import File, ManPage
from ..iterutils import first, unlistify
from ..path import Path
from ..versioning import SpecifierSet


class CopyFile(Edge):
    __modes = {'copy', 'symlink', 'hardlink'}
    msbuild_output = True

    def __init__(self, context, output, file, *, mode='copy', extra_deps=None,
                 description=None):
        if mode not in self.__modes:
            raise ValueError('unrecognized copy mode {!r}'.format(mode))

        self.mode = mode
        self.copier = context.env.tool(mode)
        self.file = file
        super().__init__(context.build, output, None, extra_deps, description)

    @staticmethod
    def convert_args(context, name, file, kwargs):
        directory = kwargs.pop('directory', None)
        if directory:
            directory = buildpath(context, directory, strict=True)
        file = context['auto_file'](file)

        def pathfn(file):
            if name is None:
                path = file.path.reroot()
                if directory:
                    return within_directory(path, directory)
                return path
            return Path(relname(context, name))

        output = file.clone(pathfn)
        return output, file, kwargs


# XXX: It might be worth generalizing this and merging it with CopyFile above,
# e.g. if we want to allow users to easily compress any kind of file in their
# build scripts.
class CompressFile(Edge):
    mode = 'gzip'

    def __init__(self, context, output, file, *, extra_deps=None,
                 description=None):
        self.copier = context.env.tool('gzip')
        self.file = file
        super().__init__(context.build, output, None, extra_deps, description)

    @staticmethod
    def convert_args(context, file, kwargs):
        file = context['auto_file'](file)

        def pathfn(file):
            return file.path.reroot().addext('.gz')

        output = file.clone(pathfn)
        return output, file, kwargs


@builtin.function()
@builtin.type(File, short_circuit=False, first_optional=True)
def copy_file(context, name, file, **kwargs):
    # Note: this only handles single files. File objects with multiple
    # related files (e.g. a DLL and its import library) will only copy the
    # primary file. In practice, this shouldn't matter, as this function is
    # mostly useful for copying data files to the build directory.
    output, file, kwargs = CopyFile.convert_args(context, name, file, kwargs)
    return CopyFile(context, output, file, **kwargs).public_output


@builtin.function()
@builtin.type(FileList, in_type=object)
def copy_files(context, files, **kwargs):
    return make_file_list(context, context['copy_file'], files, **kwargs)


@builtin.function()
@builtin.type(ManPage, short_circuit=False)
def man_page(context, name, *, compress='auto', **kwargs):
    if isinstance(name, ManPage):
        file = name
    else:
        path = context['relpath'](name)
        level = kwargs.pop('level', None)
        if level is None:
            ext = path.ext()
            if not ext[1].isdigit():
                raise ValueError('unable to guess man page level')
            level = ext[1]
        dist = kwargs.pop('dist', True)
        file = static_file(context, ManPage, name, dist, [('level', level)])

    if ( not compress or
         (compress == 'auto' and not context.env.tool('gzip').found) ):
        return file
    output, file, kwargs = CompressFile.convert_args(context, file, kwargs)
    return CompressFile(context, output, file, **kwargs).public_output


@make.rule_handler(CopyFile, CompressFile)
def make_copy_file(rule, build_inputs, buildfile, env):
    copier = rule.copier
    recipename = make.var('RULE_{}'.format(copier.rule_name.upper()))

    if hasattr(copier, 'transform_input'):
        input_var = make.qvar('1')
        args = [copier.transform_input(rule.file, rule.raw_output)]
    else:
        input_var = make.qvar('<')
        args = []

    if not buildfile.has_variable(recipename):
        buildfile.define(recipename, [copier(input_var, make.qvar('@'))])

    buildfile.rule(
        target=rule.output,
        deps=[rule.file] + rule.extra_deps,
        order_only=make.directory_deps(rule.output),
        recipe=make.Call(recipename, *args)
    )


@ninja.rule_handler(CopyFile, CompressFile)
def ninja_copy_file(rule, build_inputs, buildfile, env):
    copier = rule.copier

    variables = {}
    if rule.description:
        variables['description'] = rule.description

    if hasattr(copier, 'transform_input'):
        input_var = ninja.var('input')
        variables[input_var] = copier.transform_input(
            rule.file, rule.raw_output
        )
    else:
        input_var = ninja.var('in')

    if not buildfile.has_rule(copier.rule_name):
        desc = rule.mode + ' => ' + ninja.var('out')
        buildfile.rule(
            name=copier.rule_name,
            command=copier(input_var, ninja.var('out')),
            description=desc
        )

    buildfile.build(
        output=rule.output,
        rule=copier.rule_name,
        inputs=rule.file,
        implicit=rule.extra_deps,
        variables=variables
    )


@compdb.rule_handler(CopyFile)
def compdb_copy_file(rule, build_inputs, buildfile, env):
    copier = rule.copier

    in_file = rule.file
    if hasattr(copier, 'transform_input'):
        in_file = copier.transform_input(rule.file, rule.raw_output)
    buildfile.append(
        arguments=copier(in_file, unlistify(rule.output)),
        file=rule.file, output=first(rule.public_output)
    )


try:
    import warnings

    from ..backends.msbuild import writer as msbuild

    @msbuild.rule_handler(CopyFile)
    def msbuild_copy_file(rule, build_inputs, solution, env):
        copier = rule.copier
        if hasattr(copier, 'transform_input'):
            input = copier.transform_input(rule.file, rule.raw_output)
        else:
            input = rule.file

        extra_attrs = {}
        if rule.mode == 'symlink':
            if ( env.backend_version and env.backend_version in
                 SpecifierSet('>=15') ):
                extra_attrs['UseSymboliclinksIfPossible'] = 'true'
        elif rule.mode == 'hardlink':
            extra_attrs['UseHardlinksIfPossible'] = 'true'

        name = os.path.join('copy_file_tasks', rule.output[0].path.suffix)
        project = msbuild.CommandProject(
            env, name=name, commands=[msbuild.CommandProject.task(
                'Copy', SourceFiles=input, DestinationFiles=rule.raw_output,
                **extra_attrs
            )],
            dependencies=solution.dependencies(rule.extra_deps),
        )
        solution[rule.output[0]] = project

    @msbuild.rule_handler(CompressFile)
    def msbuild_generate_source(rule, build_inputs, solution, env):
        warnings.warn(
            'msbuild backend does not currently support compressing files'
        )  # pragma: no cover
except ImportError:  # pragma: no cover
    pass
