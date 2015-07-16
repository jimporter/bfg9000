import json
import os
import ntpath
import uuid
from lxml import etree
from lxml.builder import E

from .. import path
from .. import iterutils
from ..makedirs import makedirs

Path = path.Path

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

    def _write(self, out, depth):
        out.write('\t' * depth)
        out.write(self.name)
        if self.arg:
            out.write('({}) = {}'.format(self.arg, self.value))
        out.write('\n')

        for i in self.children:
            i._write(out, depth + 1)

        out.write('\t' * depth + 'End' + self.name + '\n')

class SlnVariable(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def _write(self, out, depth):
        out.write('\t' * depth + '{} = {}\n'.format(self.name, self.value))

class SlnMaker(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return SlnElement(*args, **kwargs)

    def __getattribute__(self, name):
        def closure(*args, **kwargs):
            return SlnElement(name, *args, **kwargs)
        return closure

def sln_write(out, x):
    if isinstance(x, list):
        for i in x:
            i._write(out, 0)
    else:
        x._write(out, 0)

def write_solution(out, uuid, projects):
    S = SlnMaker()
    Var = SlnVariable

    uuid = uuid_str(uuid)
    out.write('Microsoft Visual Studio Solution File, Format Version 12.00\n')
    out.write('# Visual Studio 14\n')

    sln = [
        Var('VisualStudioVersion', '14.0.22609.0'),
        Var('MinimumVisualStudioVersion', '10.0.40219.1')
    ]

    configs = set()
    project_info = []

    for p in projects:
        proj = S.Project(
            '"{}"'.format(uuid),
            '"{name}", "{path}", "{uuid}"'.format(
                name=p.name, path=p.path, uuid=p.uuid_str
            )
        )
        if p.dependencies:
            proj.append(
                S.ProjectSection('ProjectDependencies', 'postProject')
                 .extend(Var(i.uuid_str, i.uuid_str) for i in p.dependencies)
            )
        sln.append(proj)

        configs.add(p.config_plat)
        project_info.append(Var('{uuid}.{cfg}.ActiveCfg'.format(
            uuid=p.uuid_str, cfg=p.config_plat
        ), p.config_plat))
        project_info.append(Var('{uuid}.{cfg}.Build.0'.format(
            uuid=p.uuid_str, cfg=p.config_plat
        ), p.config_plat))

    sln.append(S.Global()(
        S.GlobalSection('SolutionConfigurationPlatforms', 'preSolution')
         .extend(Var(i, i) for i in configs),
        S.GlobalSection('ProjectConfigurationPlatforms', 'postSolution')
         .extend(project_info),
        S.GlobalSection('SolutionProperties', 'preSolution')(
            Var('HideSolutionNode', 'FALSE')
        )
    ))

    sln_write(out, sln)

_path_vars = {
    Path.srcdir: '$(SourceDir)',
    Path.builddir: None,
}
def path_str(path):
    return ntpath.normpath(path.realize(_path_vars))

class VcxProject(object):
    _XMLNS = 'http://schemas.microsoft.com/developer/msbuild/2003'
    _DOCTYPE = '<?xml version="1.0" encoding="utf-8"?>'

    def __init__(self, name, uuid, mode='Application', configuration=None,
                 platform=None, output_file=None,
                 import_lib=None, files=None, srcdir=None, libs=None,
                 libdirs=None, dependencies=None):
        self.name = name
        self.uuid = uuid
        self.mode = mode
        self.configuration = configuration or 'Debug'
        self.platform = platform or 'Win32'
        self.output_files = iterutils.listify(output_file)
        self.files = files or []
        self.srcdir = srcdir
        self.libs = libs or []
        self.libdirs = libdirs or []
        self.dependencies = dependencies or []

    @property
    def path(self):
        return os.path.join(self.name, '{}.vcxproj'.format(self.name))

    @property
    def config_plat(self):
        return '{config}|{platform}'.format(
            config=self.configuration,
            platform=self.platform
        )

    @property
    def uuid_str(self):
        return uuid_str(self.uuid)

    def write(self, out):
        override_props = E.PropertyGroup()
        if self.libdirs:
            override_props.append(E.LibraryPath(
                ';'.join(self.libdirs + ['$(LibraryPath)'])
            ))
        override_props.append(E.TargetPath(
            '$(OutDir)' + self.output_files[0]
        ))

        link = E.Link()
        if len(self.output_files) >= 1:
            link.append(E.OutputFile('$(TargetPath)'))
        if len(self.output_files) == 2:
            link.append(E.ImportLibrary('$(OutDir)' + self.output_files[1]))
        if self.libs:
            libs = ';'.join(self.libs + ['%(AdditionalDependencies)'])
            link.append(E.AdditionalDependencies(libs))

        item_defs = E.ItemDefinitionGroup(
            E.ClCompile(
                # TODO: Add more options
                E.WarningLevel('Level3')
            ),
            link
        )

        project = E.Project({'DefaultTargets': 'Build'},
                            {'ToolsVersion': '14.0'}, {'xmlns': self._XMLNS},
            E.ItemGroup({'Label' : 'ProjectConfigurations'},
                # TODO: Handle other configurations
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
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.PropertyGroup({'Label': 'Configuration'},
                E.ConfigurationType(self.mode),
                E.UseDebugLibraries('true'),
                E.PlatformToolset('v140'),
                E.CharacterSet('Multibyte')
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.props'),
            override_props,
            item_defs,
            E.ItemGroup(
                *[E.ClCompile(Include=i) for i in self.files]
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.Targets')
        )

        out.write(etree.tostring(project, doctype=self._DOCTYPE,
                                 pretty_print=True))

def link_mode(mode):
    return {
        'executable'    : 'Application',
        'static_library': 'StaticLibrary',
        'shared_library': 'DynamicLibrary',
    }[mode]

class UUIDMap(object):
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
        return { k: uuid.UUID(hex=v) for k, v in state['map'].iteritems() }

    def save(self, path=None):
        with open(path or self._path, 'w') as out:
            # Only save the UUIDs we saw this time. Skip ones we didn't see.
            seenmap = { k: v.hex for k, v in self._map.iteritems()
                        if k in self._seen }
            json.dump({
                'version': self.version,
                'map': seenmap,
            }, out)

def write(env, build_inputs):
    uuids = UUIDMap(os.path.join(env.builddir, '.bfg_uuid'))

    projects = []
    project_map = {}
    # TODO: Handle default().
    for e in build_inputs.edges:
        if type(e).__name__ == 'Link':
            # By definition, a dependency for an edge must already be defined by
            # the time the edge is created, so we can map *all* the dependencies
            # to their associated projects by looking at the projects we've
            # already created.
            dependencies = []
            for dep in e.libs:
                # TODO: It might make sense to issue a warning if we see a dep
                # we don't have a project for...
                if dep.creator and id(dep.creator.target) in project_map:
                    dependencies.append(project_map[id(dep.creator.target)])

            project = VcxProject(
                name=e.project_name,
                uuid=uuids[e.project_name],
                mode=link_mode(e.builder.mode),

                platform=env.getvar('PLATFORM'),

                # TODO: These currently end up in subdirs (e.g. bin/). We
                # probably shouldn't do this. Maybe that's more dependent on the
                # Windows platform than the MSBuild backend, though.
                output_file=[path_str(i.path) for i in
                             iterutils.iterate(e.target)],

                srcdir=env.srcdir,
                files=[path_str(i.creator.file.path) for i in e.files],
                libs=[path_str(i.path) for i in e.libs],
                libdirs=['$(OutDir)'],
                dependencies=dependencies,
            )
            projects.append(project)
            project_map[id(e.target)] = project

    with open(os.path.join(env.builddir, 'project.sln'), 'w') as out:
        write_solution(out, uuids[''], projects)
    for p in projects:
        projfile = os.path.join(env.builddir, p.path)
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
    uuids.save()
