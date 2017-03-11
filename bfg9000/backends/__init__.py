from collections import OrderedDict
from pkg_resources import iter_entry_points, DistributionNotFound

from ..objutils import memoize


@memoize
def list_backends():
    backends = []
    for i in iter_entry_points('bfg9000.backends'):
        try:
            backend = i.load()
            backends.append((i.name, backend))
        # An ImportError can be thrown by the MSBuild backend when bfg9000 was
        # installed as a Wheel with setuptools < 34.0.2. We'd require 34.0.2 or
        # better, but setuptools < 11.0 won't let you upgrade setuptools during
        # bfg's installation. Since Ubuntu 14.04 is supported until 2019 and
        # has setuptools 2.2 by default, we're stuck with this for a while.
        except (DistributionNotFound, ImportError):
            pass

    def sort_key(x):
        return x[1].priority if x[1].version() else 0
    backends.sort(key=sort_key, reverse=True)
    return OrderedDict(backends)
