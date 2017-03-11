import re

from . import builder, runner, tool, cc, jvm
from .. import shell
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..languages import language
from .common import check_which

language('java', src_exts=['.java'])
language('scala', src_exts=['.scala'])

_vars = {
    'java' : ('JAVACMD', 'JAVAC' , 'JAVAFLAGS' ),
    'scala': ('SCALACMD', 'SCALAC', 'SCALAFLAGS'),
}
_cmds = {
    'java' : ('java', ('javac', 'gcj')),
    'scala': ('scala', 'scalac'),
}


@runner('java', 'scala')
def run_java(env, lang, file):
    runner = env.builder(lang).runner
    if not runner:
        return

    if isinstance(file, Executable):
        kwargs = {'jar': True} if lang == 'java' else {}
        return runner(file, **kwargs)
    elif isinstance(file, JvmClassList):
        return runner(file.object_file)
    elif isinstance(file, ObjectFile):
        return runner(file)
    else:
        raise TypeError('expected an executable or object file for {} to run'
                        .format(lang))


@builder('java', 'scala')
def java_builder(env, lang):
    run_var, var, flags_var = _vars[lang]
    run_cmd, cmd = _cmds[lang]

    cmd = check_which(env.getvar(var, cmd), kind='{} compiler'.format(lang))
    flags = shell.split(env.getvar(flags_var, ''))

    # XXX: It might make more sense to try to check version strings instead of
    # filenames, but the command-line arg for version info can't be determined
    # ahead of time.
    if re.search(r'gcj(-\d+\.\d+)?(\.exe)?($|\s)', cmd):
        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))
        return cc.CcBuilder(env, lang, var.lower(), cmd, flags_var.lower(),
                            flags, ldflags, ldlibs)
    else:
        run_cmd = check_which(env.getvar(run_var, run_cmd),
                              kind='{} runner'.format(lang))
        jar_cmd = env.getvar('JAR', 'jar')
        jar_cmd = check_which(jar_cmd, kind='jar builder')
        return jvm.JvmBuilder(env, lang, run_var.lower(), run_cmd, var.lower(),
                              cmd, jar_cmd, flags_var.lower(), flags)
