from . import builder, cc, jvm
from .. import shell
from .common import choose_builder
from ..languages import language_vars, language_exts, lang2var

language_vars('java', compiler='JAVAC', cflags='JAVAFLAGS')
language_exts('java', source=['.java'])

language_vars('scala', compiler='SCALAC', cflags='SCALAFLAGS')
language_exts('scala', source=['.scala'])

_default_cmds = {
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}

_builders = (jvm.JvmBuilder, cc.CcBuilder)


@builder('java', 'scala')
def java_builder(env, lang):
    var, flags_var = lang2var('compiler', lang), lang2var('cflags', lang)
    candidates = env.getvar(var, _default_cmds[lang])

    flags = shell.split(env.getvar(flags_var, ''))
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
