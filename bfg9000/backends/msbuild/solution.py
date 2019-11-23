import json
import uuid
from six import iteritems

from ... import path

__all__ = ['SlnBuilder', 'SlnElement', 'SlnVariable', 'Solution', 'UuidMap']


class SlnElement(object):
    def __init__(self, name, arg=None, value=None):
        if (arg is None) != (value is None):
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
        self._project_map[key] = value

    def __getitem__(self, key):
        return self._project_map[key]

    def __iter__(self):
        return iter(self._projects)

    def __contains__(self, key):
        return key in self._project_map

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
                raise RuntimeError('unknown dependency for {!r}'.format(dep))
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


def uuid_str(uuid):
    return '{{{}}}'.format(str(uuid).upper())


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
