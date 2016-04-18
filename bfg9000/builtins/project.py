from collections import namedtuple

from .hooks import builtin
from ..build_inputs import build_input

ProjectInfo = namedtuple('ProjectInfo', ['name', 'version'])

build_input('project')(lambda build_inputs: ProjectInfo(
    build_inputs.bfgpath.parent().basename(), None
))


@builtin.globals('build_inputs')
def project(build, name, version=None):
    build['project'] = ProjectInfo(name, version)
