import os
import subprocess
import warnings
from six import string_types
from six.moves import zip

from .. import shell
from ..iterutils import listify
from ..path import Path
from ..platforms import which


class Command(object):
    def __init__(self, env, command):
        self.env = env
        self.command = command

    def run(self, *args, **kwargs):
        env = kwargs.pop('env', self.env.variables)
        # XXX: Use shell mode so that the (user-defined) command can have
        # multiple arguments defined in it?
        return subprocess.check_output(
            self(self.command, *args, **kwargs),
            universal_newlines=True, env=env
        )


class SimpleCommand(Command):
    def __init__(self, env, var, default, kind='executable'):
        command = check_which(env.getvar(var, default), env.variables, kind)
        Command.__init__(self, env, command)


def check_which(names, env=os.environ, kind='executable'):
    def transform(name):
        # Only check the first word, since some commands have built-in
        # arguments, like `mkdir -p`.
        if isinstance(name, string_types):
            return shell.split(name)[0]
        elif isinstance(name, Path):
            return name.string()
        else:
            return name

    names = listify(names)
    if len(names) == 0:
        raise TypeError('must supply at least one name')

    checks = [transform(i) for i in names]
    for name, check in zip(names, checks):
        try:
            which(check, env)
            return name
        except IOError:
            pass

    warnings.warn("unable to find {kind}{filler} {names}".format(
        kind=kind, filler='; tried' if len(names) > 1 else '',
        names=', '.join("'{}'".format(i) for i in checks)
    ))

    # Assume the first name is the best choice.
    return names[0]


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.basename())
