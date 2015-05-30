import errno
import os
import ntpath
import pickle
import uuid
from lxml import etree
from lxml.builder import E

import utils
from builtin_rules import *

def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as e:
        if not exist_ok or e.errno != errno.EEXIST or not os.path.isdir(path):
            raise

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
    configs = []

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

        configs.append(Var('{}.Debug|x86.ActiveCfg'.format(p.uuid_str),
                           'Debug|Win32'))
        configs.append(Var('{}.Debug|x86.Build.0'.format(p.uuid_str),
                           'Debug|Win32'))

    sln.append(S.Global()(
        S.GlobalSection('SolutionConfigurationPlatforms', 'preSolution')(
            Var('Debug|x86', 'Debug|x86')
        ),
        S.GlobalSection('ProjectConfigurationPlatforms', 'postSolution')
         .extend(configs),
        S.GlobalSection('SolutionProperties', 'preSolution')(
            Var('HideSolutionNode', 'FALSE')
        )
    ))

    sln_write(out, sln)

def path_str(path):
    source, pathname = path.local_path()
    if source:
        return ntpath.normpath(ntpath.join('$(SourceDir)', pathname))
    else:
        return ntpath.normpath(pathname)

class VcxProject(object):
    _XMLNS = 'http://schemas.microsoft.com/developer/msbuild/2003'
    _DOCTYPE = '<?xml version="1.0" encoding="utf-8"?>'

    def __init__(self, name, uuid, mode='Application'):
        self.name = name
        self.uuid = uuid
        self.mode = mode
        self.output_file = None
        self.import_lib = None
        self.files = []
        self.srcdir = None
        self.libs = []
        self.libdirs = []
        self.dependencies = []

    @property
    def path(self):
        return os.path.join(self.name, '{}.vcxproj'.format(self.name))

    @property
    def uuid_str(self):
        return uuid_str(self.uuid)

    def write(self, out):
        link = E.Link()
        if self.output_file:
            link.append(E.OutputFile(self.output_file))
        if self.import_lib:
            link.append(E.ImportLibrary(self.import_lib))
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

        override_props = E.PropertyGroup()
        if self.libdirs:
            override_props.append(E.LibraryPath(
                ';'.join(self.libdirs + ['$(LibraryPath)'])
            ))

        project = E.Project({'DefaultTargets': 'Build'},
                            {'ToolsVersion': '14.0'}, {'xmlns': self._XMLNS},
            E.ItemGroup({'Label' : 'ProjectConfigurations'},
                # TODO: Handle other configurations
                E.ProjectConfiguration({'Include' : 'Debug|Win32'},
                    E.Configuration('Debug'),
                    E.Platform('Win32')
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
    def __init__(self, path):
        self._path = path
        self._seen = set()
        try:
            self._map = pickle.load(open(path))
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

    def save(self, path=None):
        # Only save the UUIDs we saw this time. Skip ones we didn't see.
        seenmap = {k: v for k, v in self._map.iteritems() if k in self._seen}
        pickle.dump(seenmap, open(path or self._path, 'w'), protocol=2)

def write(env, build_inputs):
    uuids = UUIDMap(os.path.join(env.builddir, '.bfg_uuid'))

    projects = []
    project_map = {}
    # TODO: Handle default().
    for e in build_inputs.edges:
        if isinstance(e, Link):
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

            project = VcxProject(e.project_name, uuids[e.project_name],
                                 link_mode(e.builder.mode))

            # TODO: It's awfully easy to misspell these and silently fail...
            if type(e.target) == tuple:
                # TODO: These currently end up in subdirs (e.g. bin/). We
                # probably shouldn't do this. Maybe that's more dependent on the
                # Windows platform than the MSBuild backend, though.
                project.import_lib = path_str(e.target[0].path)
                project.output_file = path_str(e.target[1].path)
            else:
                project.output_file = path_str(e.target.path)

            project.srcdir = env.srcdir
            project.files = [path_str(i.creator.file.path) for i in e.files]
            project.libs = [path_str(i.path) for i in e.libs]
            project.libdirs = ['$(OutDir)']
            project.dependencies = dependencies

            projects.append(project)
            project_map[id(e.target)] = project

    with open(os.path.join(env.builddir, 'project.sln'), 'w') as out:
        write_solution(out, uuids[None], projects)
    for p in projects:
        projfile = os.path.join(env.builddir, p.path)
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
    uuids.save()
