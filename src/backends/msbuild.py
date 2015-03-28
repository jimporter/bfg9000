import os
import uuid
from lxml import etree
from lxml.builder import E

from builtin_rules import *

def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as exc:
        if not exist_ok or exc.errno != errno.EEXIST or not os.path.isdir(path):
            raise

class SlnElement(object):
    def __init__(self, name, arg=None, value=None):
        if arg is not None and value is None:
            raise TypeError('if arg is passed, value must be too')
        self.name = name
        self.arg = arg
        self.value = value
        self.children = []

    def __call__(self, *args):
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

def write_solution(out, projects):
    E = SlnMaker()
    Var = SlnVariable

    main_uuid = '986DAF6F-BAF1-40AB-9AB7-7AF8E8A7B82A' # TODO: Generate this
    out.write('Microsoft Visual Studio Solution File, Format Version 12.00\n')
    out.write('# Visual Studio 14\n')

    sln = [
        Var('VisualStudioVersion', '14.0.22609.0'),
        Var('MinimumVisualStudioVersion', '10.0.40219.1')
    ]
    configs = []

    for p in projects:
        sln.append(E.Project(
            '"{}"'.format(main_uuid),
            '"{name}", "{path}", "{uuid}"'.format(
                name=p.name, path=p.path, uuid=p.uuid_str
            )
        ))
        configs.append(Var('{}.Debug|x86.ActiveCfg'.format(p.uuid_str),
                           'Debug|Win32'))
        configs.append(Var('{}.Debug|x86.Build.0'.format(p.uuid_str),
                           'Debug|Win32'))

    sln.extend([
        E.Global()(
            E.GlobalSection('SolutionConfigurationPlatforms', 'preSolution')(
                Var('Debug|x86', 'Debug|x86')
            ),
            E.GlobalSection('ProjectConfigurationPlatforms', 'postSolution')(
                *configs
            ),
            E.GlobalSection('SolutionProperties', 'preSolution')(
                Var('HideSolutionNode', 'FALSE')
            )
        )
    ])

    sln_write(out, sln)

class VcxProject(object):
    _XMLNS = 'http://schemas.microsoft.com/developer/msbuild/2003'
    _DOCTYPE = '<?xml version="1.0" encoding="utf-8"?>'

    def __init__(self, name, files):
        self.name = name
        self.files = files

    @property
    def path(self):
        return os.path.join(self.name, '{}.vcxproj'.format(self.name))

    @property
    def uuid(self):
        return uuid.uuid3(uuid.NAMESPACE_DNS, self.name)

    @property
    def uuid_str(self):
        return '{{{}}}'.format(str(self.uuid).upper())

    def write(self, out):
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
                # TODO: Use a smarter way to make UUIDs
                E.ProjectGuid(self.uuid_str),
                E.RootNamespace(self.name)
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.default.props'),
            E.PropertyGroup({'Label': 'Configuration'},
                E.ConfigurationType('Application'), # TODO: Support libraries
                E.UseDebugLibraries('true'),
                E.PlatformToolset('v140'),
                E.CharacterSet('Multibyte')
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.props'),
            E.ItemDefinitionGroup(
                E.ClCompile(
                    # TODO: Add more options
                    E.WarningLevel('Level3')
                )
            ),
            E.ItemGroup(
                *[E.ClCompile(Include=i) for i in self.files]
            ),
            E.Import(Project='$(VCTargetsPath)\Microsoft.Cpp.Targets')
        )

        out.write(etree.tostring(project, doctype=self._DOCTYPE,
                                 pretty_print=True))

def write(env, edges):
    projects = []
    for e in edges:
        if isinstance(e, Link):
            projects.append(VcxProject(
                e.target.name, (i.creator.file.name for i in e.files)
            ))

    with open(os.path.join(env.builddir, 'project.sln'), 'w') as out:
        write_solution(out, projects)
    for p in projects:
        projfile = os.path.join(env.builddir, p.path)
        makedirs(os.path.dirname(projfile), exist_ok=True)
        with open(projfile, 'w') as out:
            p.write(out)
