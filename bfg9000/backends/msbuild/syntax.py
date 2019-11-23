import ntpath
import os
from collections import defaultdict
from enum import Enum
from itertools import chain
from lxml import etree
from lxml.builder import E
from six import iteritems, string_types

from .solution import uuid_str
from ... import path
from ... import safe_str
from ...shell import windows as wshell
from ...file_types import File
from ...iterutils import isiterable
from ...tools.common import Command

__all__ = ['BuildDir', 'CommandProject', 'NoopProject', 'Project',
           'VcxProject', 'textify', 'textify_each']

BuildDir = Enum('BuildDir', ['output', 'intermediate', 'solution'])


_path_vars = {
    BuildDir.output: {
        path.Root.srcdir: '$(SourceDir)',
        path.Root.builddir: '$(OutDir)',
    },
    BuildDir.intermediate: {
        path.Root.srcdir: '$(SourceDir)',
        path.Root.builddir: '$(IntDir)',
    },
    BuildDir.solution: {
        path.Root.srcdir: '$(SourceDir)',
        path.Root.builddir: '$(SolutionDir)',
    },
}


def textify(thing, quoted=False, builddir=BuildDir.output):
    if isinstance(thing, File):
        if thing.creator is None:
            builddir = BuildDir.solution
        elif getattr(thing.creator, 'msbuild_output', False):
            builddir = BuildDir.output
        else:
            builddir = BuildDir.intermediate

    thing = safe_str.safe_str(thing)
    if isinstance(thing, safe_str.literal_types):
        return thing.string
    elif isinstance(thing, string_types):
        return wshell.quote(thing, escape_percent=True) if quoted else thing
    elif isinstance(thing, safe_str.jbos):
        return ''.join(textify(i, quoted, builddir) for i in thing.bits)
    elif isinstance(thing, path.BasePath):
        return ntpath.normpath(thing.realize(_path_vars[builddir]))
    else:
        raise TypeError(type(thing))


def textify_each(thing, *args, **kwargs):
    return (textify(i, *args, **kwargs) for i in thing)


class Project(object):
    _XMLNS = 'http://schemas.microsoft.com/developer/msbuild/2003'
    _DOCTYPE = '<?xml version="1.0" encoding="utf-8"?>'
    _extension = '.proj'

    def __init__(self, env, name, configuration=None, dependencies=None):
        self.name = name
        self.uuid = None
        self.configuration = configuration or 'Debug'
        self.dependencies = dependencies or []

        self.version = env.getvar('VISUALSTUDIOVERSION', '14.0')

        # Some projects map one platform name to another in the .sln file (e.g.
        # "x86" => "Win32"). I'm not sure why this is, but we replicate it via
        # a "platform" and "real platform" so that C++ builds work from a VS
        # 2017 command prompt.
        self.platform = env.getvar('PLATFORM', 'Win32')
        self.real_platform = self.platform
        self.srcdir = env.srcdir

    @property
    def path(self):
        return path.Path(self.name).append('{name}{ext}'.format(
            name=os.path.basename(self.name), ext=self._extension
        ))

    def set_uuid(self, uuids):
        if not self.uuid:  # pragma: no branch
            self.uuid = uuids[self.name]

    @property
    def uuid_str(self):
        return uuid_str(self.uuid)

    @property
    def config_plat(self):
        return '{config}|{platform}'.format(
            config=self.configuration,
            platform=self.platform
        )

    @property
    def real_config_plat(self):
        return '{config}|{platform}'.format(
            config=self.configuration,
            platform=self.real_platform
        )

    def _write(self, out, children):
        project = E.Project({'DefaultTargets': 'Build',
                             'ToolsVersion': self.version,
                             'xmlns': self._XMLNS},
            E.ItemGroup({'Label': 'ProjectConfigurations'},
                E.ProjectConfiguration({'Include' : self.real_config_plat},
                    E.Configuration(self.configuration),
                    E.Platform(self.real_platform)
                )
            ),
            E.PropertyGroup({'Label': 'Globals'},
                E.ProjectGuid(self.uuid_str),
                E.RootNamespace(self.name),
                E.Platform(self.real_platform),
                E.SourceDir(textify(self.srcdir))
            ),
            *children
        )
        out.write(etree.tostring(project, doctype=self._DOCTYPE,
                                 pretty_print=True))


class VcxProject(Project):
    _extension = '.vcxproj'

    _warning_levels = {
        '0'  : 'TurnOffAllWarnings',
        '1'  : 'Level1',
        '2'  : 'Level2',
        '3'  : 'Level3',
        '4'  : 'Level4',
        'all': 'EnableAllWarnings',
    }

    def __init__(self, env, name, mode='Application', configuration=None,
                 output_file=None, files=None, compile_options=None,
                 link_options=None, dependencies=None):
        Project.__init__(self, env, name, configuration, dependencies)
        self.mode = mode
        self.output_file = output_file
        self.files = files or []
        self.compile_options = compile_options or {}
        self.link_options = link_options or {}

        version = env.getvar('VCTOOLSVERSION', self.version)
        self.toolset = 'v' + version.replace('.', '')[0:3]

        # As above, VS 2017 remaps x86 to Win32 for C++ projects.
        if self.real_platform == 'x86':
            self.real_platform = 'Win32'

    def write(self, out):
        target_name = safe_str.safe_str(self.output_file).basename()
        override_props = E.PropertyGroup(
            E.TargetName(os.path.splitext(target_name)[0]),
            E.TargetPath(textify(self.output_file))
        )

        compile_opts = E.ClCompile()
        self._write_compile_options(compile_opts, self.compile_options)
        link_opts = E.Lib() if self.mode == 'StaticLibrary' else E.Link()
        self._write_link_options(link_opts, self.link_options)

        self._write(out, [
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.PropertyGroup({'Label': 'Configuration'},
                E.ConfigurationType(self.mode),
                E.UseDebugLibraries('true'),
                E.PlatformToolset(self.toolset),
                E.CharacterSet('Multibyte')
            ),
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.props'),
            override_props,
            E.ItemDefinitionGroup(compile_opts, link_opts),
            self._compiles(self.files),
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.Targets')
        ])

    def _compiles(self, files):
        def basename(path):
            return path.stripext().basename()

        # First, figure out all the common prefixes of files with the same
        # basename so we can use this to give them unique object names.
        names = defaultdict(lambda: [])
        for i in self.files:
            p = i['name'].path
            names[basename(p)].append(p.parent())
        prefixes = {k: path.commonprefix(v) if len(v) > 1 else None
                    for k, v in iteritems(names)}

        compiles = E.ItemGroup()
        for i in self.files:
            name = i['name']
            c = E.ClCompile(Include=textify(name))
            self._write_compile_options(c, i['options'])

            prefix = prefixes[basename(name.path)]
            if prefix:
                # If this prefix is shared with another file, strip it out to
                # create a unique directory to store this object file.
                suffix = path.Path(name.path.relpath(prefix)).stripext('.obj')
                c.append(E.ObjectFileName(textify(
                    suffix, builddir=BuildDir.intermediate
                )))
            compiles.append(c)
        return compiles

    def _write_compile_options(self, element, options):
        warnings = options.get('warnings', {})
        if warnings.get('level') is not None:
            element.append(E.WarningLevel(
                self._warning_levels[warnings['level']]
            ))
        if warnings.get('as_error') is not None:
            element.append(E.TreatWarningAsError(
                'true' if warnings['as_error'] else 'false'
            ))

        if options.get('includes'):
            element.append(E.AdditionalIncludeDirectories( ';'.join(chain(
                textify_each(options['includes']),
                ['%(AdditionalIncludeDirectories)']
            )) ))

        if options.get('defines'):
            element.append(E.PreprocessorDefinitions( ';'.join(chain(
                textify_each(options['defines']),
                ['%(PreprocessorDefinitions)']
            )) ))

        pch = options.get('pch', {})
        if pch.get('create') is not None:
            element.append(E.PrecompiledHeader('Create'))
            element.append(E.PrecompiledHeaderFile(pch['create']))
        elif pch.get('use') is not None:
            element.append(E.PrecompiledHeader('Use'))
            element.append(E.PrecompiledHeaderFile(pch['use']))

        if options.get('extra'):
            element.append(E.AdditionalOptions( ' '.join(chain(
                textify_each(options['extra'], quoted=True),
                ['%(AdditionalOptions)']
            )) ))

    def _write_link_options(self, element, options):
        element.append(E.OutputFile('$(TargetPath)'))

        if options.get('import_lib'):
            element.append(E.ImportLibrary(
                textify(options['import_lib'])
            ))

        if options.get('extra'):
            element.append(E.AdditionalOptions( ' '.join(chain(
                textify_each(options['extra'], quoted=True),
                ['%(AdditionalOptions)']
            )) ))

        if options.get('libs'):
            element.append(E.AdditionalDependencies( ';'.join(chain(
                textify_each(options['libs']),
                ['%(AdditionalDependencies)']
            )) ))


class NoopProject(Project):
    def write(self, out):
        self._write(out, [E.Target(Name='Build')])


class CommandProject(Project):
    def __init__(self, env, name, configuration=None, commands=None,
                 dependencies=None, makedir='$(OutDir)'):
        Project.__init__(self, env, name, configuration, dependencies)
        self.commands = commands or []
        self.makedir = makedir

    @staticmethod
    def convert_attr(value):
        if isiterable(value):
            return ';'.join(textify_each(value, quoted=True))
        else:
            return textify(value)

    @staticmethod
    def convert_command(value):
        value = Command.convert_args(value, lambda x: x.command)
        return ' '.join(textify_each(value, quoted=True))

    @classmethod
    def task(cls, task, **kwargs):
        return E(task, **{k: cls.convert_attr(v)
                          for k, v in iteritems(kwargs)})

    def write(self, out):
        target = E.Target(Name='Build')
        if self.makedir:
            target.append(E.MakeDir(Directories=self.makedir))

        for line in self.commands:
            if not isinstance(line, etree._Element):  # pragma: no cover
                raise TypeError('expected an lxml element')
            target.append(line)

        self._write(out, [
            # Import the C++ properties to get $(OutDir). There might be a
            # better way to handle this.
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.props'),
            target
        ])
