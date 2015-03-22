class Node(object):
    def __init__(self, name, deps=None):
        self.name = name
        self.deps = [blah(i, Node, dependency) for i in deps or []]

class dependency(Node):
    def __init__(self, name):
        Node.__init__(self, name)
        self.kind = 'dependency'

def blah(x, valid_type, creator=None, **kwargs):
    if isinstance(x, valid_type):
        return x
    elif creator:
        return creator(x)
    else:
        return valid_type(x, **kwargs)

all_targets = []
