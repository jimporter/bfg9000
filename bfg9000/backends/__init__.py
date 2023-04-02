import importlib_metadata as metadata
from collections import OrderedDict

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
    return OrderedDict(backends)
