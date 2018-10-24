import json
import ntpath
import os
import uuid
from collections import defaultdict
from enum import Enum
from itertools import chain
from lxml import etree
from lxml.builder import E
from six import iteritems, string_types

from ... import path
from ... import safe_str
from ...shell import windows as wshell
from ...file_types import File
from ...iterutils import isiterable
from ...tools.common import Command

__all__ = ['BuildDir', 'ExecProject', 'NoopProject', 'Solution', 'UuidMap',
           'VcxProject', 'textify', 'textify_each']

BuildDir = Enum('BuildDir', ['output', 'intermediate', 'solution'])


def uuid_str(uuid):
    return '{{{}}}'.format(str(uuid).upper())


class SlnElement(object):
    def __init__(self, name, arg=None, value=None):
        if arg is not None and value is None:
            raise TypeError('if arg is passed, value must be too')
        self.name = name
        self.arg = arg
        self.value = value
        self.children = []

    def __call__(self, *args):
        return self.extend(args)

    def append(self, item):
        self.children.append(item)
        return self

    def extend(self, args):
        self.children.extend(args)
        return self

    def write(self, out, depth=0):
        out.write('\t' * depth)
        out.write(self.name)
        if self.arg:
            out.write('({}) = {}'.format(self.arg, self.value))
        out.write('\n')

        for i in self.children:
            i.write(out, depth + 1)

        out.write('\t' * depth + 'End' + self.name + '\n')


class SlnVariable(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def write(self, out, depth=0):
        out.write('\t' * depth + '{} = {}\n'.format(self.name, self.value))


class SlnBuilder(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return SlnElement(*args, **kwargs)

    def __getattribute__(self, name):
        def closure(*args, **kwargs):
            return SlnElement(name, *args, **kwargs)
        return closure


class Solution(object):
    def __init__(self, uuids):
        self.uuid = uuids['']
        self._uuids = uuids
        self._projects = []
        self._project_map = {}

    def __setitem__(self, key, value):
        value.set_uuid(self._uuids)
        self._projects.append(value)
        self._project_map[id(key)] = value

    def __getitem__(self, key):
        return self._project_map[id(key)]

    def __iter__(self):
        return iter(self._projects)

    def __contains__(self, key):
        return id(key) in self._project_map

    def dependencies(self, deps):
        # By definition, a dependency for an edge must already be defined by
        # the time the edge is created, so we can map *all* the dependencies to
        # their associated projects by looking at the projects we've already
        # created.
        dependencies = []
        for dep in deps:
            if not dep.creator:
                continue

            dep_output = dep.creator.output[0]
            if dep_output not in self:
                raise ValueError('unknown dependency for {!r}'.format(dep))
            dependencies.append(self[dep_output])
        return dependencies

    @property
    def uuid_str(self):
        return uuid_str(self.uuid)

    def write(self, out):
        S = SlnBuilder()
        Var = SlnVariable

        out.write('Microsoft Visual Studio Solution File, Format Version ' +
                  '12.00\n')
        out.write('# Visual Studio 14\n')

        Var('VisualStudioVersion', '14.0.22609.0').write(out)
        Var('MinimumVisualStudioVersion', '10.0.40219.1').write(out)

        configs = set()
        project_info = []

        for p in self._projects:
            path_vars = {path.Root.builddir: None}
            proj = S.Project(
                '"{}"'.format(self.uuid_str),
                '"{name}", "{path}", "{uuid}"'.format(
                    name=p.name, path=p.path.string(path_vars), uuid=p.uuid_str
                )
            )
            if p.dependencies:
                proj.append(
                    S.ProjectSection('ProjectDependencies', 'postProject')
                     .extend(Var(i.uuid_str, i.uuid_str)
                             for i in p.dependencies)
                )
            proj.write(out)

            configs.add(p.config_plat)
            project_info.append(Var('{uuid}.{cfg}.ActiveCfg'.format(
                uuid=p.uuid_str, cfg=p.config_plat
            ), p.real_config_plat))
            project_info.append(Var('{uuid}.{cfg}.Build.0'.format(
                uuid=p.uuid_str, cfg=p.config_plat
            ), p.real_config_plat))

        S.Global()(
            S.GlobalSection('SolutionConfigurationPlatforms', 'preSolution')
             .extend(Var(i, i) for i in configs),
            S.GlobalSection('ProjectConfigurationPlatforms', 'postSolution')
             .extend(project_info),
            S.GlobalSection('SolutionProperties', 'preSolution')(
                Var('HideSolutionNode', 'FALSE')
            )
        ).write(out)


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
        if not self.uuid:
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
                suffix = path.Path(name.path.relpath(prefix))
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
        self._write(out, [E.Target({'Name': 'Build'})])


class ExecProject(Project):
    def __init__(self, env, name, configuration=None, commands=None,
                 dependencies=None):
        Project.__init__(self, env, name, configuration, dependencies)
        self.commands = commands or []

    def write(self, out):
        target = E.Target({'Name': 'Build'},
            E.MakeDir(Directories='$(OutDir)')
        )
        for line in self.commands:
            if isiterable(line):
                line = Command.convert_args(line, lambda x: x.command)
                cmd = ' '.join(textify_each(line, quoted=True))
            else:
                cmd = textify(line)
            target.append(E.Exec({
                'Command': cmd, 'WorkingDirectory': '$(OutDir)'
            }))

        self._write(out, [
            # Import the C++ properties to get $(OutDir). There might be a
            # better way to handle this.
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.Import(Project=r'$(VCTargetsPath)\Microsoft.Cpp.props'),
            target
        ])


class UuidMap(object):
    version = 1

    def __init__(self, path):
        self._path = path
        self._seen = set()
        try:
            self._map = self._load(path)
        except IOError:
            self._map = {}

    def __getitem__(self, key):
        self._seen.add(key)
        if key in self._map:
            return self._map[key]
        else:
            u = uuid.uuid4()
            self._map[key] = u
            return u

    @classmethod
    def _load(cls, path):
        with open(path) as inp:
            state = json.load(inp)
        if state['version'] > cls.version:
            raise ValueError('saved version exceeds expected version')
        return { k: uuid.UUID(hex=v) for k, v in iteritems(state['map']) }

    def save(self, path=None):
        with open(path or self._path, 'w') as out:
            # Only save the UUIDs we saw this time. Skip ones we didn't see.
            seenmap = { k: v.hex for k, v in iteritems(self._map)
                        if k in self._seen }
            json.dump({
                'version': self.version,
                'map': seenmap,
            }, out)
