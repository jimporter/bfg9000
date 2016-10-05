import os

from .. import safe_str
from .. import shell
from .hooks import builder
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..iterutils import iterate, uniques
from ..languages import language
from ..path import Path, Root
from .utils import check_which

language('java', src_exts=['.java'])


class JavaBuilder(object):
    def __init__(self, env, command, jar_command):
        self.brand = 'java'
        self.compiler = JavaCompiler(env, command)
        self._linkers = {
            'executable': JarMaker(env, jar_command, Executable),
            'shared_library': JarMaker(env, jar_command, SharedLibrary),
        }

    def linker(self, mode):
        return self._linkers[mode]


class JavaCompiler(object):
    def __init__(self, env, command):
        self.rule_name = self.command_var = 'javac'
        self.command = command
        self.global_args = shell.split(env.getvar('JAVACFLAGS', ''))

    @property
    def deps_flavor(self):
        return None

    @property
    def num_outputs(self):
        return 1

    @property
    def depends_on_libs(self):
        return True

    def __call__(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend([input, '-d', '.'])
        return result

    def _class_path(self, libraries):
        dirs = uniques(i.path for i in iterate(libraries))
        if dirs:
            return ['-cp', safe_str.join(dirs, os.pathsep)]
        return []

    def args(self, options, output, pkg=False):
        libraries = getattr(options, 'libs', [])
        return self._class_path(libraries)

    def link_args(self, mode, defines):
        return []

    def output_file(self, name, options):
        return ObjectFile(Path(name + '.class', Root.builddir),
                          'jvm', 'java')


class JarMaker(object):
    def __init__(self, env, command, output_type):
        self.rule_name = self.command_var = self.link_var = 'jar'
        self.command = command
        self.output_type = output_type
        self.global_args = []
        self.global_libs = []

    def can_link(self, format, langs):
        return format == 'jvm'

    @property
    def num_outputs(self):
        return 1

    def pre_build(self, build, options, name):
        dirs = uniques(i.path for i in iterate(options.libs))
        text = ['Class-Path: {}'.format(
            os.pathsep.join(i.basename() for i in dirs)
        )]
        if getattr(options, 'entry_point', None):
            text.append('Main-Class: {}'.format(options.entry_point))

        source = File(Path(name + '-manifest.txt'))
        WriteFile(build, source, text)
        options.manifest = source

    def __call__(self, cmd, input, output, manifest, libs=None, args=None):
        result = [cmd, 'cfm', output, manifest]
        result.extend(iterate(input))
        return result

    def args(self, options, output, pkg=False):
        return []

    def always_libs(self, primary):
        return []

    def libs(self, options, output, pkg=False):
        return []

    def output_file(self, name, options):
        path = Path(name + '.jar', Root.builddir)
        return self.output_type(path, 'jvm')


@builder('java')
def java_builder(env):
    cmd = env.getvar('JAVAC', 'javac')
    cmd = check_which(cmd, kind='java compiler')

    jar_cmd = env.getvar('JAR', 'jar')
    jar_cmd = check_which(jar_cmd, kind='jar builder')

    return JavaBuilder(env, cmd, jar_cmd)
