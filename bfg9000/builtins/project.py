from collections import namedtuple

from . import builtin
from ..build_inputs import build_input

ProjectInfo = namedtuple('ProjectInfo', ['name', 'version'])

build_input('project')(lambda build_inputs, env: ProjectInfo(
    env.srcdir.basename(), None
))


@builtin.function('build_inputs')
def project(build, name, version=None):
    build['project'] = ProjectInfo(name, version)
