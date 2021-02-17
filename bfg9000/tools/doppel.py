from . import tool
from .common import not_buildroot, SimpleCommand

from ..iterutils import iterate


@tool('doppel')
class Doppel(SimpleCommand):
    def __init__(self, env):
        super().__init__(env, name='doppel', env_var='DOPPEL',
                         default='doppel')

    def kind_args(self, kind):
        if kind == 'data':
            return ['-m', '644']
        elif kind == 'program':
            return []
        raise ValueError('unknown kind {!r}'.format(kind))

    def _call_onto(self, cmd, src, dst):
        return cmd + ['-p', src, dst]

    def _call_into(self, cmd, src, dst, *, directory=None):
        result = cmd + ['-ipN']
        if not_buildroot(directory):
            result.extend(['-C', directory])
        result.extend(iterate(src))
        result.append(dst)
        return result

    def _call_archive(self, cmd, src, dst, *, format, directory=None,
                      dest_prefix=None):
        result = cmd + ['-ipN', '-f', format]
        if not_buildroot(directory):
            result.extend(['-C', directory])
        if dest_prefix:
            result.extend(['-P', dest_prefix])
        result.extend(iterate(src))
        result.append(dst)
        return result

    def _call(self, cmd, mode, *args, **kwargs):
        try:
            return getattr(self, '_call_' + mode)(cmd, *args, **kwargs)
        except AttributeError:
            raise TypeError('unknown mode {!r}'.format(mode))
