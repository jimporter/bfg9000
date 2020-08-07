from collections import OrderedDict
from itertools import chain

from .path import Path, Root
from .file_types import Directory, File, Node
from .iterutils import iterate, listify, unlistify
from .objutils import objectify

_build_inputs = {}


def build_input(name):
    def wrapper(fn):
        if name in _build_inputs:  # pragma: no cover
            raise ValueError("'{}' already registered".format(name))
        _build_inputs[name] = fn
        return fn
    return wrapper


class Edge:
    def __init__(self, build, output, final_output=None, extra_deps=None,
                 description=None):
        self.description = description
        self.raw_output = output
        self.output = listify(output)
        for i in self.output:
            i.creator = self

        self.public_output = unlistify([
            i for i in listify(final_output) or self.output if not i.private
        ])

        def make(name):
            path = Path.ensure(name, Root.srcdir)
            f = Directory(path) if path.directory else File(path)
            if f.path.root == Root.srcdir:
                return build.add_source(f)
            return f

        self.extra_deps = [objectify(i, Node, make, (str, Path))
                           for i in iterate(extra_deps)]
        build.add_edge(self)


class BuildInputs:
    def __init__(self, env, bfgpath):
        self._sources = OrderedDict()
        self.bootstrap_paths = []
        self._edges = []
        self._extra_targets = []
        self._extra_inputs = {}

        self.bfgpath = bfgpath
        self.add_bootstrap(bfgpath)

        for name, fn in _build_inputs.items():
            self._extra_inputs[name] = fn(self, env)

    def add_bootstrap(self, path):
        self.bootstrap_paths.append(path)
        return path

    def add_source(self, source):
        self._sources[source.path] = source
        return source

    def add_edge(self, edge):
        self._edges.append(edge)
        return edge

    def add_target(self, target):
        self._extra_targets.append(target)
        return target

    def sources(self):
        return chain((File(i) for i in self.bootstrap_paths),
                     self._sources.values())

    def targets(self):
        return chain(
            chain.from_iterable(i.output for i in self._edges),
            self._extra_targets
        )

    def edges(self):
        return iter(self._edges)

    def __getitem__(self, key):
        return self._extra_inputs[key]

    def __setitem__(self, key, value):
        self._extra_inputs[key] = value
