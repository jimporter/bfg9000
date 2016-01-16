from six import iteritems

from .file_types import File, Node, sourcify
from .iterutils import iterate


_build_inputs = {}


def build_input(name):
    def wrapper(fn):
        if name in _build_inputs:
            raise ValueError('"{}" already registered'.format(name))
        _build_inputs[name] = fn
        return fn
    return wrapper


class Edge(object):
    def __init__(self, build, target, extra_deps=None):
        for t in target.all:
            t.creator = self
        self.target = target

        self.extra_deps = [sourcify(i, Node, File)
                           for i in iterate(extra_deps)]
        build.add_edge(self)


class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.extra_inputs = {}

        for name, fn in iteritems(_build_inputs):
            self.extra_inputs[name] = fn()

    def add_edge(self, edge):
        self.edges.append(edge)

    def __getitem__(self, key):
        return self.extra_inputs[key]
