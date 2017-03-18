from . import builder, cc, jvm
from .. import shell
from .common import choose_builder
from ..languages import language

language('java', src_exts=['.java'])
language('scala', src_exts=['.scala'])

_vars = {
    'java' : ('JAVAC' , 'JAVAFLAGS' ),
    'scala': ('SCALAC', 'SCALAFLAGS'),
}
_default_cmds = {
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}

_builders = (jvm.JvmBuilder, cc.CcBuilder)


@builder('java', 'scala')
def java_builder(env, lang):
    var, flags_var = _vars[lang]
    candidates = env.getvar(var, _default_cmds[lang])

    flags = shell.split(env.getvar(flags_var, ''))
    return choose_builder(env, lang, candidates, _builders, var.lower(),
                          flags_var.lower(), flags)
