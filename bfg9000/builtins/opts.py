from . import builtin
from .. import options
from ..objutils import memoize


class Options(object):
    def __init__(self, options):
        self._options = options

    def __getattr__(self, key):
        return self._options[key]


@builtin.getter()
@memoize
def opts():
    return Options(options.Option.registry)
