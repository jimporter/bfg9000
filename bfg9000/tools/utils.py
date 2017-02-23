import os
import subprocess
import warnings
from six.moves import zip

from .. import shell
from ..file_types import Package
from ..iterutils import isiterable, listify
from ..path import Path, which


class Command(object):
    def __init__(self, env, command):
        self.env = env
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
    def __init__(self, env, var, default, kind='executable'):
        command = check_which(env.getvar(var, default), env.variables, kind)
        Command.__init__(self, env, command)


class SystemPackage(Package):
    def __init__(self, name, includes=None, lib_dirs=None, libraries=None,
                 version=None):
        Package.__init__(self, name)
        self.includes = includes or []
        self.lib_dirs = lib_dirs or []
        self.libs = libraries or []
        self.version = version

    def cflags(self, compiler, output):
        return compiler.args(self, output, pkg=True)

    def ldflags(self, linker, output):
        return linker.args(self, output, pkg=True)

    def ldlibs(self, linker, output):
        return linker.libs(self, output, pkg=True)


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
