from collections import OrderedDict
from itertools import chain
from six import iteritems, itervalues

from .path import Path, Root
from .file_types import File, Node
from .iterutils import iterate, listify, unlistify
from .objutils import objectify

_build_inputs = {}


def build_input(name):
    def wrapper(fn):
        if name in _build_inputs:
            raise ValueError("'{}' already registered".format(name))
        _build_inputs[name] = fn
        return fn
    return wrapper


class Edge(object):
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
            return build.add_source(File(Path(name, Root.srcdir)))
        self.extra_deps = [objectify(i, Node, make)
                           for i in iterate(extra_deps)]
        build.add_edge(self)


class BuildInputs(object):
    def __init__(self, env, bfgpath):
        self.bfgpath = bfgpath
        self._sources = OrderedDict([ (bfgpath, File(bfgpath)) ])
        self._edges = []
        self._extra_targets = []
        self._extra_inputs = {}

        for name, fn in iteritems(_build_inputs):
            self._extra_inputs[name] = fn(self, env)

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
        return itervalues(self._sources)

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
