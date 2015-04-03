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
        self._default_targets = []
        self.fallback_default = None

    def add_edge(self, edge):
        self.edges.append(edge)

    @property
    def default_targets(self):
        if self._default_targets:
            return self._default_targets
        elif self.fallback_default:
            return [self.fallback_default]
        else:
            return []

    @default_targets.setter
    def default_targets(self, value):
        self._default_targets = value
