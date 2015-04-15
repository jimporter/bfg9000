class Node(object):
    def __init__(self, name, creator=None):
        self.name = name
        self.creator = creator

    @property
    def is_source(self):
        return self.creator is None

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.name)
        )

class Edge(object):
    def __init__(self, target, deps=None):
        target.creator = self
        self.target = target
        self.deps = [nodeify(i, Node) for i in deps or []]

def nodeify(x, valid_type, creator=None, **kwargs):
    if isinstance(x, valid_type):
        return x
    elif creator:
        return creator(x)
    else:
        return valid_type(x, **kwargs)

class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.default_targets = []
        self.install_targets = []
        self.fallback_default = None

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_default_targets(self):
        if self.default_targets:
            return self.default_targets
        elif self.fallback_default:
            return [self.fallback_default]
        else:
            return []
