import os
import subprocess
import warnings
from six.moves import zip

from .. import shell
from ..iterutils import isiterable, listify
from ..path import Path, which


class Command(object):
    def __init__(self, env, rule_name, command_var, command):
        self.env = env
        self.rule_name = rule_name
        self.command_var = command_var
        self.command = command

    @staticmethod
    def convert_args(args, conv, in_place=None):
        if not isiterable(args):
            raise TypeError('expected a list of command-line arguments')

        if in_place is None:
            in_place = not any(isinstance(i, Command) for i in args)
        if not in_place:
            args = type(args)(args)
        for i, v in enumerate(args):
            if isinstance(v, Command):
                args[i] = conv(v)
        return args

    def __call__(self, *args, **kwargs):
        cmd = kwargs.pop('cmd', self)
        return self._call(cmd, *args, **kwargs)

    def run(self, *args, **kwargs):
        env = self.env.variables
        if 'env' in kwargs:
            if kwargs.pop('env_update', True):
                env = env.copy()
                env.update(kwargs.pop('env'))
            else:
                env = kwargs.pop('env')

        # XXX: Use shell mode so that the (user-defined) command can have
        # multiple arguments defined in it?
        return shell.execute(self.convert_args(
            self(*args, **kwargs), lambda x: x.command, True
        ), env=env, stderr=shell.Mode.devnull)

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.command)


class SimpleCommand(Command):
    def __init__(self, env, name, env_var, default, kind='executable'):
        cmd = check_which(env.getvar(env_var, default), env.variables, kind)
        Command.__init__(self, env, name, name, cmd)


def check_which(names, env=os.environ, kind='executable'):
    names = listify(names)
    try:
        return which(names, env, first_word=True)
    except IOError:
        warnings.warn("unable to find {kind}{filler} {names}".format(
            kind=kind, filler='; tried' if len(names) > 1 else '',
            names=', '.join("'{}'".format(i) for i in names)
        ))

        # Assume the first name is the best choice.
        return names[0]


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.suffix)
