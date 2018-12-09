from . import builder, cc, jvm
from .common import choose_builder
from ..languages import known_formats, known_langs

with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', runner='JAVACMD', flags='JAVAFLAGS')
    x.exts(source=['.java'])

with known_langs.make('scala') as x:
    x.vars(compiler='SCALAC', runner='SCALACMD', flags='SCALAFLAGS')
    x.exts(source=['.scala'])

with known_formats.make('jvm', mode='dynamic') as x:
    x.vars(linker='JAR', flags='JARFLAGS')

_default_cmds = {
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}

_builders = (jvm.JvmBuilder, cc.CcBuilder)


@builder('java', 'scala')
def java_builder(env, lang):
    return choose_builder(env, known_langs[lang], _default_cmds[lang],
                          _builders)
