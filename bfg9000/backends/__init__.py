import importlib_metadata as metadata

from ..objutils import memoize


@memoize
def list_backends():
    backends = []
    for i in metadata.entry_points(group='bfg9000.backends'):
        try:
            backend = i.load()
            backends.append((i.name, backend))
        except ModuleNotFoundError:
            pass

    def sort_key(x):
        return x[1].priority if x[1].version() else 0
    backends.sort(key=sort_key, reverse=True)
    return dict(backends)


class BuildRuleHandler:
    def __init__(self):
        self.handlers = {}

    def __call__(self, *args):
        def decorator(fn):
            for i in args:
                self.handlers[i] = fn
            return fn
        return decorator

    def run(self, edges, *args, **kwargs):
        for e in edges:
            self.handlers[type(e)](e, *args, **kwargs)


class BuildHook:
    def __init__(self):
        self.hooks = []

    def __call__(self, fn):
        self.hooks.append(fn)
        return fn

    def run(self, *args, **kwargs):
        for i in self.hooks:
            i(*args, **kwargs)
