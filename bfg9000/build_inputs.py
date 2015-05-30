from . import path
from . import utils

class Node(object):
    def __init__(self):
        self.creator = None

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

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
    def __init__(self, target, extra_deps=None):
        for t in utils.iterate(target):
            t.creator = self
        self.target = target

        def make_dep(x):
            return File(x, path.Path.srcdir)
        self.extra_deps = [utils.objectify(i, Node, make_dep)
                           for i in utils.iterate(extra_deps)]

class InstallInputs(object):
    def __init__(self):
        self.files = []
        self.directories = []

    def __nonzero__(self):
        return bool(self.files or self.directories)

class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.default_targets = []
        self.fallback_default = None
        self.install_targets = InstallInputs()
        self.test_targets = []
        self.all_tests = []
        self.global_options = {}

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_default_targets(self):
        if self.default_targets:
            return self.default_targets
        elif self.fallback_default:
            return utils.listify(self.fallback_default)
        else:
            return []
