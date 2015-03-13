class Node(object):
    def __init__(self, name, kind, deps, attrs):
        self.name = name
        self.kind = kind
        self.deps = deps
        self._attrs = attrs

    def __getitem__(self, key):
        return self._attrs[key]

    def __contains__(self, key):
        return key in self._attrs[key]

all_targets = []

def rule(fn):
    def wrapped(name, deps=None, **kwargs):
        result = Node(name, fn.func_name,
                      nodeify_list(deps or [], 'dependency'), fn(**kwargs))
        all_targets.append(result)
        return result
    wrapped.func_name = fn.func_name
    return wrapped

def nodeify(thing, kind):
    if isinstance(thing, Node):
        # Check if `kind` matches?
        return thing
    return Node(thing, kind, [], {})

def nodeify_list(iterable, kind):
    return [nodeify(i, kind) for i in iterable]
