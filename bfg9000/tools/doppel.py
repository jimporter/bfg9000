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

    def _call(self, cmd, mode, src, dst, directory=None, format=None,
              dest_prefix=None):
        if mode == 'onto':
            return cmd + ['-p', src, dst]

        elif mode == 'into':
            result = cmd + ['-ipN']
            if not_buildroot(directory):
                result.extend(['-C', directory])
            result.extend(iterate(src))
            result.append(dst)
            return result

        elif mode == 'archive':
            result = cmd + ['-ipN', '-f', format]
            if not_buildroot(directory):
                result.extend(['-C', directory])
            if dest_prefix:
                result.extend(['-P', dest_prefix])
            result.extend(iterate(src))
            result.append(dst)
            return result

        raise ValueError('unknown mode {!r}'.format(mode))
