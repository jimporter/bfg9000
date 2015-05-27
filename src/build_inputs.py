import path
import utils

class Node(object):
    install_root = path.Path.basedir

    def __init__(self, name, source):
        self.path = path.Path(name, source, self.install_root)
        self.creator = None

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

class File(Node):
    # TODO: Remove this and just use Node's ctor?
    def __init__(self, name, source=path.Path.builddir):
        Node.__init__(self, name, source)

class Directory(File):
    pass

class Phony(Node):
    def __init__(self, name):
        Node.__init__(self, name, path.Path.builddir)

class Edge(object):
    def __init__(self, target, deps=None):
        for t in utils.iterate(target):
            t.creator = self
        self.target = target
        self.deps = [utils.objectify(i, Node) for i in utils.iterate(deps)]

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
