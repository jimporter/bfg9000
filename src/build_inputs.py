import utils

class Node(object):
    def __init__(self, path):
        self.path = path
        self.creator = None

    @property
    def is_source(self):
        return self.creator is None

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

class File(Node):
    def __init__(self, raw_name, path=None):
        Node.__init__(self, path if path is not None else raw_name)
        self.raw_name = raw_name

class Directory(File):
    pass

class Edge(object):
    def __init__(self, target, deps=None):
        target.creator = self
        self.target = target
        self.deps = utils.objectify_list(deps, Node)

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
            return [self.fallback_default]
        else:
            return []
