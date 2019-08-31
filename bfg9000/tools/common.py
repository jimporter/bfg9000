import os
import re
import warnings
from six import iteritems

from .. import options as opts
from .. import path, shell
from ..iterutils import first, iterate, listify, slice_dict

_modes = {
    'shared_library': 'EXPORTS',
    'static_library': 'STATIC',
}

_macro_ex = re.compile(r'([^A-Za-z0-9_]|^(?=[0-9]))')
_macro_ex2 = re.compile(r'^_')


def library_macro(name, mode):
    # Replace all non-alphanumeric characters in the name with underscores and
    # prepend an underscore if the name starts with a digit. Then add an extra
    # 'LIB' to the beginning if the transformed name starts with an underscore.
    return '{name}_{suffix}'.format(
        name=_macro_ex2.sub('LIB_', _macro_ex.sub('_', name.upper())),
        suffix=_modes[mode]
    )


def not_buildroot(thing):
    if isinstance(thing, path.BasePath):
        return thing != type(thing)('.')
    return thing is not None


class Builder(object):
    def __init__(self, lang, brand, version):
        self.lang = lang
        self.brand = brand
        self.version = version

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.brand)


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

    @property
    def brand(self):
        return self.builder.brand

    @property
    def version(self):
        return self.builder.version

    @property
    def flavor(self):
        return self.builder.flavor

    @property
    def num_outputs(self):
        return 'all'

    def pre_build(self, build, name, context):
        return opts.option_list()

    def post_build(self, build, options, output, context):
        return None

    def post_install(self, options, output, context):
        return None


def check_which(names, *args, **kwargs):
    names = listify(names)
    try:
        return shell.which(names, *args, **kwargs)
    except IOError as e:
        warnings.warn(str(e))
        # Assume the first name is the best choice.
        return shell.listify(names[0])


def choose_builder(env, langinfo, default_candidates, builders):
    candidates = listify(env.getvar(langinfo.var('compiler'),
                                    default_candidates))
    try:
        cmd = shell.which(candidates, env.variables,
                          kind='{} compiler'.format(langinfo.name))
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
                          .format(langinfo.name, tried))

    return builder_type(env, langinfo, cmd, output)


def darwin_install_name(library):
    return os.path.join('@rpath', library.path.suffix)
