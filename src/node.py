class Node(object):
    def __init__(self, name):
        self.name = name

class Edge(object):
    def __init__(self, target, deps=None):
        self.target = target
        self.deps = [nodeify(i, Node) for i in deps or []]
        all_edges.append(self)

def nodeify(x, valid_type, creator=None, **kwargs):
    if isinstance(x, valid_type):
        return x
    elif creator:
        return creator(x)
    else:
        return valid_type(x, **kwargs)

all_edges = []
