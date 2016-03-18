import json
import ntpath
import os
import uuid
from collections import defaultdict
from itertools import chain
from lxml import etree
from lxml.builder import E
from six import iteritems, string_types

from ... import path
from ... import safe_str
from ... import shell
from ...iterutils import isiterable

__all__ = ['ExecProject', 'Solution', 'UuidMap', 'VcxProject', 'textify',
           'textify_each']


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
            proj = S.Project(
                '"{}"'.format(self.uuid_str),
                '"{name}", "{path}", "{uuid}"'.format(
                    name=p.name, path=p.path, uuid=p.uuid_str
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
            ), p.config_plat))
            project_info.append(Var('{uuid}.{cfg}.Build.0'.format(
                uuid=p.uuid_str, cfg=p.config_plat
            ), p.config_plat))

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
    False: {
        path.Root.srcdir: '$(SourceDir)',
        path.Root.builddir: '$(IntDir)',
    },
    True: {
        path.Root.srcdir: '$(SourceDir)',
        path.Root.builddir: '$(OutDir)',
    },
}


def textify(thing, quoted=False, out=False):
    thing = safe_str.safe_str(thing)

    if isinstance(thing, safe_str.escaped_str):
        return thing.string
    elif isinstance(thing, string_types):
        return shell.quote(thing) if quoted else thing
    elif isinstance(thing, safe_str.jbos):
        return ''.join(textify(i, quoted, out) for i in thing.bits)
    elif isinstance(thing, path.Path):
        return ntpath.normpath(thing.realize(_path_vars[out]))
    else:
        raise TypeError(type(thing))


def textify_each(thing, quoted=False, out=False):
    return (textify(i, quoted, out) for i in thing)


class Project(object):
    _XMLNS = 'http://schemas.microsoft.com/developer/msbuild/2003'
    _DOCTYPE = '<?xml version="1.0" encoding="utf-8"?>'
    _extension = '.proj'

    def __init__(self, name, uuid=None, version=None, configuration=None,
                 platform=None, srcdir=None, dependencies=None):
        self.name = name
        self.uuid = uuid
        self.version = version or '14.0'
        self.configuration = configuration or 'Debug'
        self.platform = platform or 'Win32'
        self.srcdir = srcdir
        self.dependencies = dependencies or []

    @property
    def path(self):
        return os.path.join(self.name, '{name}{ext}'.format(
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

    def _write(self, out, children):
        project = E.Project({'DefaultTargets': 'Build',
                             'ToolsVersion': self.version,
                             'xmlns': self._XMLNS},
            E.ItemGroup({'Label': 'ProjectConfigurations'},
                E.ProjectConfiguration({'Include' : self.config_plat},
                    E.Configuration(self.configuration),
                    E.Platform(self.platform)
                )
            ),
            E.PropertyGroup({'Label': 'Globals'},
                E.ProjectGuid(self.uuid_str),
                E.RootNamespace(self.name),
                E.SourceDir(ntpath.normpath(self.srcdir))
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

    def __init__(self, name, uuid=None, version=None, configuration=None,
                 platform=None, srcdir=None, mode='Application',
                 output_file=None, import_lib=None, files=None, libs=None,
                 options=None, dependencies=None):
        Project.__init__(self, name, uuid, version, configuration, platform,
                         srcdir, dependencies)
        self.mode = mode
        self.output_file = output_file
        self.import_lib = import_lib
        self.files = files or []
        self.libs = libs or []
        self.options = options or {}

    @property
    def toolset(self):
        return 'v' + self.version.replace('.', '')

    def write(self, out):
        target_name = safe_str.safe_str(self.output_file).basename()
        override_props = E.PropertyGroup(
            E.TargetName(os.path.splitext(target_name)[0]),
            E.TargetPath(textify(self.output_file, out=True))
        )

        compile_opts = E.ClCompile()
        warnings = self.options.get('warnings', {})
        if warnings.get('level') is not None:
            compile_opts.append(E.WarningLevel(
                self._warning_levels[warnings['level']]
            ))
        if warnings.get('as_error') is not None:
            compile_opts.append(E.TreatWarningAsError(
                'true' if warnings['as_error'] else 'false'
            ))
        if self.options.get('includes'):
            compile_opts.append(E.AdditionalIncludeDirectories( ';'.join(chain(
                textify_each(self.options['includes']),
                ['%(AdditionalIncludeDirectories)']
            )) ))
        if self.options.get('defines'):
            compile_opts.append(E.PreprocessorDefinitions(
                ';'.join(textify_each(self.options['defines']))
            ))
        if self.options.get('compile'):
            compile_opts.append(E.AdditionalOptions( ' '.join(chain(
                textify_each(self.options['compile'], quoted=True),
                ['%(AdditionalOptions)']
            )) ))

        link_opts = E.Lib() if self.mode == 'StaticLibrary' else E.Link()
        link_opts.append(E.OutputFile('$(TargetPath)'))
        if self.import_lib:
            link_opts.append(E.ImportLibrary(
                textify(self.import_lib, out=True)
            ))
        if self.options.get('link'):
            link_opts.append(E.AdditionalOptions( ' '.join(chain(
                textify_each(self.options['link'], quoted=True, out=True),
                ['%(AdditionalOptions)']
            )) ))
        if self.libs:
            link_opts.append(E.AdditionalDependencies( ';'.join(chain(
                textify_each(self.libs, out=True),
                ['%(AdditionalDependencies)']
            )) ))

        names = defaultdict(lambda: [])
        for i in self.files:
            basename = ntpath.splitext(i.path.basename())[0]
            names[basename].append(i.path.parent())

        compiles = E.ItemGroup()
        for i in self.files:
            c = E.ClCompile(Include=textify(i))
            dupes = names[ ntpath.splitext(i.path.basename())[0] ]
            if len(dupes) > 1:
                # XXX: This can still fail rarely if the paths' bases are
                # different.
                prefix = ntpath.commonprefix([j.suffix for j in dupes])
                suffix = path.Path(i.path.parent().suffix[len(prefix):])
                c.append(E.ObjectFileName(textify(suffix) + '\\'))
            compiles.append(c)

        self._write(out, [
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.PropertyGroup({'Label': 'Configuration'},
                E.ConfigurationType(self.mode),
                E.UseDebugLibraries('true'),
                E.PlatformToolset(self.toolset),
                E.CharacterSet('Multibyte')
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.props'),
            override_props,
            E.ItemDefinitionGroup(compile_opts, link_opts),
            compiles,
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.Targets')
        ])


class ExecProject(Project):
    def __init__(self, name, uuid=None, version=None, configuration=None,
                 platform=None, srcdir=None, commands=None, dependencies=None):
        Project.__init__(self, name, uuid, version, configuration, platform,
                         srcdir, dependencies)
        self.commands = commands or []

    def write(self, out):
        target = E.Target({'Name': 'Build'},
            E.MakeDir(Directories='$(OutDir)')
        )
        for i in self.commands:
            # XXX: What to do here with the `out` param? It's not clear what
            # value it should have; do users want to mess with an intermediate
            # file or an output file?
            if isiterable(i):
                cmd = ' '.join(textify_each(i, quoted=True, out=True))
            else:
                cmd = textify(i, out=True)
            target.append(E.Exec({'Command': cmd,
                                  'WorkingDirectory': '$(OutDir)'}))

        self._write(out, [
            # Import the C++ properties to get $(OutDir). There might be a
            # better way to handle this.
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.props'),
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
