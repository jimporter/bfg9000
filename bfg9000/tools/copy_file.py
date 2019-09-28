from . import tool
from .common import SimpleCommand


class LinkCommand(SimpleCommand):
    def __init__(self, *args, **kwargs):
        SimpleCommand.__init__(self, *args, **kwargs)
        lower_cmd = [i.lower() for i in self.command]
        self.flavor = 'mklink' if 'mklink' in lower_cmd else 'ln'

    def _call(self, cmd, input, output):
        if self.flavor == 'mklink':
            return cmd + [output, input]
        return cmd + [input, output]


@tool('symlink')
class Symlink(LinkCommand):
    def __init__(self, env):
        default = ('cmd /c mklink' if env.host_platform.family == 'windows'
                   else 'ln -sf')
        LinkCommand.__init__(self, env, name='symlink', env_var='SYMLINK',
                             default=default)

    def transform_input(self, input, output):
        try:
            return input.path.relpath(output.path.parent())
        except ValueError:
            return input.path


@tool('hardlink')
class Hardlink(LinkCommand):
    def __init__(self, env):
        default = ('cmd /c mklink /H' if env.host_platform.family == 'windows'
                   else 'ln -f')
        LinkCommand.__init__(self, env, name='hardlink', env_var='HARDLINK',
                             default=default)


@tool('copy')
class Copy(SimpleCommand):
    def __init__(self, env):
        default = ('cmd /c copy' if env.host_platform.family == 'windows'
                   else 'cp -f')
        SimpleCommand.__init__(self, env, name='cp', env_var='CP',
                               default=default)

    def _call(self, cmd, input, output):
        return cmd + [input, output]
