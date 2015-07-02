from . import find
from . import path
from .utils import iterate, listify, objectify
from .safe_str import safe_str

class Node(object):
    def __init__(self):
        self.creator = None

    def _safe_str(self):
        return safe_str(self.path)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

def sourcify(thing, valid_type, make_type=None, **kwargs):
    return objectify(thing, valid_type, make_type, source=path.Path.srcdir,
                     **kwargs)

class File(Node):
    install_root = path.Path.basedir

    def __init__(self, name, source):
        Node.__init__(self)
        self.path = path.Path(name, source, self.install_root)

class Directory(File):
    pass

class Phony(Node):
    def __init__(self, name):
        Node.__init__(self)
        self.path = name

class Edge(object):
    def __init__(self, build, target, extra_deps=None):
        for t in iterate(target):
            t.creator = self
        self.target = target

        self.extra_deps = [sourcify(i, Node, File) for i in iterate(extra_deps)]
        build.add_edge(self)

class InstallInputs(object):
    def __init__(self):
        self.files = []
        self.directories = []

    def __nonzero__(self):
        return bool(self.files or self.directories)

class TestInputs(object):
    def __init__(self):
        self.tests = []
        self.targets = []
        self.extra_deps = []

    def __nonzero__(self):
        return bool(self.tests)

class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.default_targets = []
        self.fallback_default = None
        self.install_targets = InstallInputs()
        self.tests = TestInputs()
        self.global_options = {}
        self.global_link_options = []
        self.find_results = find.FindCache()

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_default_targets(self):
        if self.default_targets:
            return self.default_targets
        elif self.fallback_default:
            return listify(self.fallback_default)
        else:
            return []
