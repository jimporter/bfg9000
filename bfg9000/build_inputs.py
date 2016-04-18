from six import iteritems

from .path import Path, Root
from .file_types import File, Node, objectify
from .iterutils import iterate, listify, unlistify

_build_inputs = {}


def build_input(name):
    def wrapper(fn):
        if name in _build_inputs:
            raise ValueError('"{}" already registered'.format(name))
        _build_inputs[name] = fn
        return fn
    return wrapper


class Edge(object):
    def __init__(self, build, output, extra_deps=None):
        self.output = listify(output)
        for i in self.output:
            i.creator = self
        self.public_output = unlistify([
            i for i in self.output if not i.private
        ])

        def make(name):
            return build.add_source(File(Path(name, Root.srcdir)))
        self.extra_deps = [objectify(i, Node, make)
                           for i in iterate(extra_deps)]
        build.add_edge(self)


class BuildInputs(object):
    def __init__(self, bfgpath):
        self.bfgpath = bfgpath
        self.sources = [File(bfgpath)]
        self.edges = []
        self.extra_inputs = {}

        for name, fn in iteritems(_build_inputs):
            self.extra_inputs[name] = fn(self)

    def add_source(self, source):
        self.sources.append(source)
        return source

    def add_edge(self, edge):
        self.edges.append(edge)
        return edge

    def __getitem__(self, key):
        return self.extra_inputs[key]

    def __setitem__(self, key, value):
        self.extra_inputs[key] = value
