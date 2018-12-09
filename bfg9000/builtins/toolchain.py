from six import iteritems

from . import builtin
from .. import path, platforms, shell
from ..iterutils import first, isiterable
from ..languages import known_formats, known_langs
from ..shell import posix as pshell

_unsafe_builtins = ['file', '__import__', 'input', 'open', 'raw_input',
                    'reload']


@builtin.getter(name='__builtins__', context='toolchain')
def builtins():
    return {k: v for k, v in iteritems(__builtins__)
            if k not in _unsafe_builtins}


@builtin.getter('env', context='toolchain')
def environ(env):
    return env.variables


@builtin.function('env', context='toolchain')
def target_platform(env, platform=None, arch=None):
    env.target_platform = platforms.target.platform_info(platform, arch)


@builtin.function(context='toolchain')
def which(names, resolve=False, strict=True, kind='executable'):
    try:
        return ' '.join(shell.which(names, resolve=resolve, kind=kind))
    except IOError:
        if strict:
            raise
        result = first(names)
        return pshell.join(result) if isiterable(result) else result


@builtin.function('env', context='toolchain')
def compiler(env, names, lang, strict=False):
    var = known_langs[lang].var('compiler')
    env.variables[var] = which(names, strict=strict, kind='compiler')


@builtin.function('env', context='toolchain')
def compile_options(env, options, lang):
    # This only supports strings (and lists of strings) for options, *not*
    # semantic options. It would be nice if we could support semantic options,
    # but we'd either need to know the flavor of compiler at this point (we
    # don't) or we'd have to store the options in some way other than as an
    # environment variable.
    if isiterable(options):
        options = pshell.join(options)
    env.variables[known_langs[lang].var('flags')] = options


@builtin.function('env', context='toolchain')
def runner(env, names, lang, strict=False):
    var = known_langs[lang].var('runner')
    env.variables[var] = which(names, strict=strict, kind='runner')


@builtin.function('env', context='toolchain')
def linker(env, names, format='native', mode='dynamic', strict=False):
    var = known_formats[format, mode].var('linker')
    env.variables[var] = which(names, strict=strict, kind='linker')


@builtin.function('env', context='toolchain')
def link_options(env, options, format='native', mode='dynamic'):
    # As above, this only supports strings (and lists of strings) for options,
    # *not* semantic options.
    if isiterable(options):
        options = pshell.join(options)
    env.variables[known_formats[format, mode].var('flags')] = options


@builtin.function('env', context='toolchain')
def lib_options(env, options, format='native', mode='dynamic'):
    # As above, this only supports strings (and lists of strings) for options,
    # *not* semantic options.
    if isiterable(options):
        options = pshell.join(options)
    env.variables[known_formats[format, mode].var('libs')] = options


@builtin.function('env', context='toolchain')
def install_dirs(env, **kwargs):
    for k, v in iteritems(kwargs):
        env.install_dirs[path.InstallRoot[k]] = path.abspath(v)
