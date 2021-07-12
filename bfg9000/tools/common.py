import re
import warnings

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


# Make a function to convert between command names for different languages in
# the same family (e.g. # `gcc` => `g++`). If no entry in the mapping matches
# the command, we return None to indicate that the conversion has failed.
def make_command_converter(mapping):
    def escape(i):
        if isinstance(i, str):
            return '({})'.format(re.escape(i))
        if i.groups:
            raise re.error('capturing groups not allowed')
        return '({})'.format(i.pattern)

    sub = '|'.join(escape(i[0]) for i in mapping)
    ex = re.compile(r'(?:^|(?<=\W))(?:{})(?:$|(?=\W))'.format(sub))

    def fn(cmd):
        s, n = ex.subn(lambda m: mapping[m.lastindex - 1][1], cmd)
        return s if n > 0 else None

    return fn


def make_command_converter_pair(mapping):
    inverse = [(v, k) for k, v in mapping]
    return make_command_converter(mapping), make_command_converter(inverse)


def not_buildroot(thing):
    if isinstance(thing, path.BasePath):
        return thing != type(thing)('.')
    return thing is not None


class Builder:
    def __init__(self, lang, brand, version):
        self.lang = lang
        self.brand = brand
        self.version = version

    def __repr__(self):
        return '<{}({!r})>'.format(type(self).__name__, self.brand)


class Command:
    def __init__(self, env, rule_name=None, *, command):
        self.env = env
        self.command_var, self.command, self.found = command
        self.rule_name = rule_name or self.command_var

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

    def __call__(self, *args, cmd=None, **kwargs):
        cmd = listify(cmd or self)
        return self._call(cmd, *args, **kwargs)

    def run(self, *args, **kwargs):
        run_kwargs = slice_dict(kwargs, ('env', 'extra_env', 'stdout',
                                         'stderr'))
        run_kwargs.setdefault('stdout', shell.Mode.pipe)
        if run_kwargs['stdout'] != shell.Mode.normal:
            run_kwargs.setdefault('stderr', shell.Mode.devnull)

        return self.env.execute(self(*args, **kwargs), **run_kwargs)

    def __repr__(self):
        return '<{}({})>'.format(
            type(self).__name__, ', '.join(repr(i) for i in self.command)
        )


class SimpleCommand(Command):
    def __init__(self, env, name, env_var, default, kind='executable'):
        cmd, found = check_which(env.getvar(env_var, default),
                                 env.variables, kind=kind)
        super().__init__(env, command=(name, cmd, found))


class BuildCommand(Command):
    def __init__(self, builder, env, rule_name=None, *, command, **kwargs):
        super().__init__(env, rule_name, command=command)
        self.builder = builder

        # Fill in the names and values of the various flags needed for this
        # command, e.g. `flags` ('cflags', 'ldflags'), `libs` ('ldlibs'), etc.
        for k, v in kwargs.items():
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

    def pre_output(self, context, name, step):
        return opts.option_list()

    def post_output(self, context, options, output, step):
        return None

    def post_install(self, options, output, step):
        return None


class SimpleBuildCommand(BuildCommand):
    def __init__(self, builder, env, *, command, flags):
        super().__init__(builder, env, command=command, flags=flags)


def guess_command(sibling, converter):
    for i in sibling.command:
        guessed_cmd = converter(i)
        if guessed_cmd is not None:
            return guessed_cmd
    return None


def check_which(names, *args, **kwargs):
    names = listify(names)
    try:
        return shell.which(names, *args, **kwargs), True
    except IOError as e:
        warnings.warn(str(e))
        # Assume the first name is the best choice.
        return shell.listify(names[0]), False


def choose_builder(env, langinfo, builders, *, candidates=None,
                   default_candidates=None, fallback_builder=None,
                   strict=False):
    if candidates is None:
        candidates = env.getvar(langinfo.var('compiler'), default_candidates)
    candidates = listify(candidates)

    try:
        cmd = shell.which(candidates, env.variables,
                          kind='{} compiler'.format(langinfo.name))
        found = True
    except IOError as e:
        if strict:
            raise
        warnings.warn(str(e))
        cmd = shell.listify(candidates[0])
        builder_type = fallback_builder or first(builders)
        output = ''
        found = False
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

    return builder_type(env, langinfo, cmd, found, output)
