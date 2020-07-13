from . import builtin
from .. import platforms, shell
from ..iterutils import first, isiterable
from ..languages import known_formats, known_langs
from ..path import Path, Root, InstallRoot
from ..shell import posix as pshell

_unsafe_builtins = ['file', '__import__', 'input', 'open', 'raw_input',
                    'reload']


@builtin.getter(name='__builtins__', context='toolchain')
def builtins(context):
    return {k: v for k, v in __builtins__.items()
            if k not in _unsafe_builtins}


@builtin.getter(context='toolchain')
def environ(context):
    return context.env.variables


@builtin.getter(context='toolchain')
def srcdir(context):
    # Make a copy of the srcdir object, since it should be read-only.
    return context.env.srcdir.reroot(context.env.srcdir.root)


@builtin.function(context='toolchain')
def target_platform(context, platform=None, arch=None):
    env = context.env
    env.target_platform = platforms.target.platform_info(platform, arch)


@builtin.function(context='toolchain')
def which(context, names, resolve=False, strict=True, kind='executable'):
    try:
        return ' '.join(shell.which(names, resolve=resolve, kind=kind))
    except IOError:
        if strict:
            raise
        result = first(names)
        return pshell.join(result) if isiterable(result) else result


@builtin.function(context='toolchain')
def compiler(context, names, lang, strict=False):
    var = known_langs[lang].var('compiler')
    compiler = context['which'](names, strict=strict, kind='compiler')
    context.env.variables[var] = compiler


@builtin.function(context='toolchain')
def compile_options(context, options, lang):
    # This only supports strings (and lists of strings) for options, *not*
    # semantic options. It would be nice if we could support semantic options,
    # but we'd either need to know the flavor of compiler at this point (we
    # don't) or we'd have to store the options in some way other than as an
    # environment variable.
    if isiterable(options):
        options = pshell.join(options)
    context.env.variables[known_langs[lang].var('flags')] = options


@builtin.function(context='toolchain')
def runner(context, names, lang, strict=False):
    var = known_langs[lang].var('runner')
    runner = context['which'](names, strict=strict, kind='runner')
    context.env.variables[var] = runner


@builtin.function(context='toolchain')
def linker(context, names, format='native', mode='dynamic', strict=False):
    var = known_formats[format][mode].var('linker')
    linker = context['which'](names, strict=strict, kind='linker')
    context.env.variables[var] = linker


@builtin.function(context='toolchain')
def link_options(context, options, format='native', mode='dynamic'):
    # As above, this only supports strings (and lists of strings) for options,
    # *not* semantic options.
    if isiterable(options):
        options = pshell.join(options)
    context.env.variables[known_formats[format][mode].var('flags')] = options


@builtin.function(context='toolchain')
def lib_options(context, options, format='native', mode='dynamic'):
    # As above, this only supports strings (and lists of strings) for options,
    # *not* semantic options.
    if isiterable(options):
        options = pshell.join(options)
    context.env.variables[known_formats[format][mode].var('libs')] = options


@builtin.function(context='toolchain')
def install_dirs(context, **kwargs):
    if context.reload:
        return
    env = context.env
    for k, v in kwargs.items():
        env.install_dirs[InstallRoot[k]] = Path.ensure(v, Root.absolute)
