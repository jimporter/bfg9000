from . import builtin
from ..build_inputs import build_input
from ..iterutils import default_sentinel


@build_input('project')
class ProjectInfo:
    def __init__(self, build_inputs, env):
        self.name = env.srcdir.basename()
        self.version = None
        self._options = {
            'intermediate_dirs': True,
            'lang': 'c',
            'find_exclude': ['.*#', '*~', '#*#'],
        }

    def __getitem__(self, key):
        return self._options[key]

    def __setitem__(self, key, value):
        if key not in self._options:
            raise KeyError('unknown option {!r}'.format(key))
        self._options[key] = value


@builtin.function()
def project(context, name=default_sentinel, version=default_sentinel,
            **kwargs):
    info = context.build['project']
    if name is not default_sentinel:
        info.name = name
    if version is not default_sentinel:
        info.version = version

    for k, v in kwargs.items():
        info[k] = v
