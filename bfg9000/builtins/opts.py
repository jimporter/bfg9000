from . import builtin
from .. import options


class Options:
    def __init__(self, options):
        self._options = options

    def __getattr__(self, key):
        return self._options[key]


@builtin.getter()
def opts(context):
    return Options(options.Option.registry)
