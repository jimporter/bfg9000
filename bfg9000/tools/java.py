from . import builder, cc, jvm
from .. import shell
from .common import choose_builder
from ..languages import known_langs

with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', runner='JAVACMD', cflags='JAVAFLAGS')
    x.exts(source=['.java'])

with known_langs.make('scala') as x:
    x.vars(compiler='SCALAC', runner='SCALACMD', cflags='SCALAFLAGS')
    x.exts(source=['.scala'])

_default_cmds = {
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}

_builders = (jvm.JvmBuilder, cc.CcBuilder)


@builder('java', 'scala')
def java_builder(env, lang):
    return choose_builder(env, known_langs[lang], _default_cmds[lang],
                          _builders)
