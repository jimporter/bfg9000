import re

from . import cc, jvm
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
    'java' : ['javac', 'gcj'],
    'scala': 'scalac',
}


@builder('java', 'scala')
def java_builder(env, lang):
    var, flags_var = _vars[lang]
    low_var, low_flags_var = var.lower(), flags_var.lower()

    cmd = env.getvar(var, _cmds[lang])
    cmd = check_which(cmd, kind='{} compiler'.format(lang))
    flags = shell.split(env.getvar(flags_var, ''))

    # XXX: It might make more sense to try to check version strings instead of
    # filenames, but the command-line arg for version info can't be determined
    # ahead of time.
    if re.search(r'gcj(-\d+\.\d+)?(\.exe)?($|\s)', cmd):
        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))
        return cc.CcBuilder(env, lang, low_var, cmd, low_flags_var, flags,
                            ldflags, ldlibs)
    else:
        jar_cmd = env.getvar('JAR', 'jar')
        jar_cmd = check_which(jar_cmd, kind='jar builder')
        return jvm.JvmBuilder(env, lang, low_var, cmd, jar_cmd, low_flags_var,
                              flags)
