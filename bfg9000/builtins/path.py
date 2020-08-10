import re

from . import builtin
from .. import path as _path
from ..iterutils import map_iterable


for i in (_path.Root, _path.InstallRoot):
    builtin.default(context='*')(i)
builtin.default(context='*', name='Path')(_path.Path)


@builtin.function(context=('build', 'options'))
def path_exists(context, path):
    return _path.exists(context['relpath'](path), context.env.base_dirs)


@builtin.function(context=('build', 'options'))
def relpath(context, path, strict=False):
    return _path.Path.ensure(path, context.path.parent(), strict=strict)


def relname(context, name):
    return map_iterable(lambda i: context['relpath'](i).suffix, name)


def buildpath(context, path, strict=False):
    base = context.path.parent().reroot()
    return _path.Path.ensure(path, base, strict=strict)


def within_directory(path, directory):
    suffix = path.relpath(directory.parent(), localize=False)
    suffix = re.sub(r'(^|/)..(?=/|$)', r'\1PAR', suffix)
    return directory.append(suffix)
