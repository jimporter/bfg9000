import os
import subprocess
import warnings
from six import iteritems
from six.moves import zip

from .. import shell
from ..iterutils import isiterable, listify, reverse_enumerate
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

        for i, v in reverse_enumerate(args):
            if isinstance(v, Command):
                c = conv(v)
                if isiterable(c):
                    args[i : i + 1] = c
                else:
                    args[i] = c
        return args

    def __call__(self, *args, **kwargs):
        cmd = listify(kwargs.pop('cmd', self))
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
        return '<{}({})>'.format(
            type(self).__name__, ', '.join(repr(i) for i in self.command)
        )


class SimpleCommand(Command):
    def __init__(self, env, name, env_var, default, kind='executable'):
        cmd = check_which(env.getvar(env_var, default), env.variables,
                          kind=kind)
        Command.__init__(self, env, name, name, cmd)


class BuildCommand(Command):
    def __init__(self, builder, env, rule_name, command_var, command,
                 **kwargs):
        Command.__init__(self, env, rule_name, command_var, command)
        self.builder = builder

        # Fill in the names and values of the various flags needed for this
        # command, e.g. `flags` ('cflags', 'ldflags'), `libs` ('ldlibs'), etc.
        for k, v in iteritems(kwargs):
            setattr(self, '{}_var'.format(k), v[0])
            setattr(self, 'global_{}'.format(k), v[1])

    @property
    def lang(self):
        return self.builder.lang


def check_which(names, *args, **kwargs):
    names = listify(names)
    try:
        return which(names, *args, **kwargs)
    except IOError as e:
        warnings.warn(str(e))
        # Assume the first name is the best choice.
        return shell.listify(names[0])


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.suffix)
