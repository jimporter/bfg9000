import os
import subprocess
import warnings
from six import iteritems
from six.moves import zip

from .. import shell
from ..iterutils import first, isiterable, iterate, listify, slice_dict
from ..path import Path


class Command(object):
    def __init__(self, env, rule_name, command_var, command):
        self.env = env
        self.rule_name = rule_name
        self.command_var = command_var
        self.command = command

    @staticmethod
    def convert_args(args, conv):
        args = listify(args, scalar_ok=False)
        if not any(isinstance(i, Command) for i in args):
            return args

        result = type(args)()
        for i in args:
            if isinstance(i, Command):
                result.extend(listify(conv(i)))
            else:
                result.append(i)
        return result

    def __call__(self, *args, **kwargs):
        cmd = listify(kwargs.pop('cmd', self))
        return self._call(cmd, *args, **kwargs)

    def run(self, *args, **kwargs):
        run_kwargs = slice_dict(kwargs, ('env', 'env_update'))

        return self.env.execute(
            self(*args, **kwargs), stdout=shell.Mode.pipe,
            stderr=shell.Mode.devnull, **run_kwargs
        )

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

    @property
    def family(self):
        return self.builder.family


def check_which(names, *args, **kwargs):
    names = listify(names)
    try:
        return shell.which(names, *args, **kwargs)
    except IOError as e:
        warnings.warn(str(e))
        # Assume the first name is the best choice.
        return shell.listify(names[0])


def choose_builder(env, lang, candidates, builders, cmd_var, *args, **kwargs):
    candidates = listify(candidates)
    try:
        cmd = shell.which(candidates, env.variables,
                          kind='{} compiler'.format(lang))
    except IOError as e:
        warnings.warn(str(e))
        cmd = shell.listify(candidates[0])
        builder_type = first(builders)
        output = ''
    else:
        for builder_type in builders:
            try:
                output = builder_type.check_command(env, cmd)
                break
            except Exception:
                pass
        else:
            tried = ', '.join(repr(i) for i in iterate(candidates))
            raise IOError('no working {} compiler found; tried {}'
                          .format(lang, tried))

    return builder_type(env, lang, cmd_var, cmd, *args, version_output=output,
                        **kwargs)


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.suffix)
