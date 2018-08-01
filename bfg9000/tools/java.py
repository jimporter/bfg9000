from . import builder, cc, jvm
from .. import shell
from .common import choose_builder
from ..languages import language, lang2cmd, lang2flags

language('java', cmd_var='JAVAC', flags_var='JAVAFLAGS', src_exts=['.java'])
language('scala', cmd_var='SCALAC', flags_var='SCALAFLAGS',
         src_exts=['.scala'])

_default_cmds = {
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}

_builders = (jvm.JvmBuilder, cc.CcBuilder)


@builder('java', 'scala')
def java_builder(env, lang):
    var, flags_var = lang2cmd[lang], lang2flags[lang]
    candidates = env.getvar(var, _default_cmds[lang])

    flags = shell.split(env.getvar(flags_var, ''))
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
