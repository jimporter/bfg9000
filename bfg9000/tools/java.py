from . import jvm
from .. import shell
from .hooks import builder
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..languages import language
from .utils import check_which

language('java', src_exts=['.java'])
language('scala', src_exts=['.scala'])

_vars = {
    'java' : ('JAVAC' , 'JAVAFLAGS' ),
    'scala': ('SCALAC', 'SCALAFLAGS'),
}
_cmds = {
    'java' : 'javac',
    'scala': 'scalac',
}


@builder('java', 'scala')
def java_builder(env, lang):
    var, flags_var = _vars[lang]
    low_var, low_flags_var = var.lower(), flags_var.lower()

    cmd = env.getvar(var, _cmds[lang])
    cmd = check_which(cmd, kind='{} compiler'.format(lang))
    flags = shell.split(env.getvar(flags_var, ''))

    jar_cmd = env.getvar('JAR', 'jar')
    jar_cmd = check_which(jar_cmd, kind='jar builder')

    return jvm.JvmBuilder(env, lang, low_var, cmd, jar_cmd, low_flags_var,
                          flags)
