import os
import re
from itertools import chain

from .common import BuildCommand, check_which
from .. import safe_str
from .. import shell
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Path, Root


class JvmBuilder(object):
    def __init__(self, env, lang, name, command, flags_name, flags,
                 version_output):
        self.lang = lang
        self.object_format = 'jvm'
        self.brand = 'jvm'  # XXX: Be more specific?

        jar_command = check_which(env.getvar('JAR', 'jar'), kind='jar builder')

        # XXX: This works sort of by coincidence, since it's trivial to predict
        # the runner's name based on the lang. Be smarter here?
        run_name = lang.upper() + 'CMD'
        run_command = check_which(env.getvar(run_name, lang),
                                  kind='{} runner'.format(lang))

        self.compiler = JvmCompiler(self, env, name, command, flags_name,
                                    flags)
        self._linker = JarMaker(self, env, jar_command)
        self.packages = JvmPackageResolver(self, env, run_command)
        self.runner = JvmRunner(self, env, run_name, run_command)

    @staticmethod
    def check_command(env, command):
        return shell.execute(command + ['-version'], env=env.variables,
                             stderr=shell.Mode.devnull)

    @property
    def flavor(self):
        return 'jvm'

    @property
    def can_dual_link(self):
        return False

    def linker(self, mode):
        if mode == 'static_library':
            raise ValueError('static linking not supported with {}'.format(
                self.brand
            ))
        if mode not in ('executable', 'shared_library'):
            raise KeyError(mode)
        return self._linker


class JvmCompiler(BuildCommand):
    def __init__(self, builder, env, name, command, flags_name, flags):
        BuildCommand.__init__(self, builder, env, name, name, command,
                              flags=(flags_name, flags))

    @property
    def flavor(self):
        return 'jvm'

    @property
    def deps_flavor(self):
        return None

    @property
    def depends_on_libs(self):
        return True

    @property
    def accepts_pch(self):
        return False

    def _call(self, cmd, input, output, flags=None):
        jvmoutput = self.env.tool('jvmoutput')
        result = list(chain(
            cmd, self._always_flags, iterate(flags), [input]
        ))
        return jvmoutput(output, result)

    @property
    def _always_flags(self):
        return ['-verbose', '-d', '.']

    def _class_path(self, libraries):
        dirs = uniques(i.path for i in iterate(libraries))
        if dirs:
            return ['-cp', safe_str.join(dirs, os.pathsep)]
        return []

    def flags(self, options, output, pkg=False):
        libraries = getattr(options, 'libs', [])
        return self._class_path(libraries)

    def link_flags(self, mode, defines):
        return []

    def output_file(self, name, options):
        return JvmClassList(ObjectFile(
            Path(name + '.classlist'), self.builder.object_format, self.lang
        ))


class JarMaker(BuildCommand):
    flags_var = 'jarflags'

    def __init__(self, builder, env, command):
        global_flags = shell.split(env.getvar('JARFLAGS', 'cfm'))
        BuildCommand.__init__(self, builder, env, 'jar', 'jar', command,
                              flags=('jarflags', global_flags))

    @property
    def flavor(self):
        return 'jar'

    @property
    def family(self):
        return 'jvm'

    def can_link(self, format, langs):
        return format == 'jvm'

    @property
    def has_link_macros(self):
        return False

    def pre_build(self, build, options, name):
        # Fix up paths for the Class-Path field: escape spaces, use forward
        # slashes on Windows, and prefix Windows drive letters with '/' to
        # disambiguate them from URLs.
        def fix_path(p):
            if self.env.platform.name == 'windows':
                if p[1] == ':':
                    p = '/' + p
                p = p.replace('\\', '/')
            return p.replace(' ', '%20')

        libs = getattr(options, 'libs', [])
        libs = sum((i.libs for i in getattr(options, 'packages', [])), libs)

        dirs = uniques(i.path for i in libs)
        base = Path(name).parent()
        text = ['Class-Path: {}'.format(
            ' '.join(fix_path(i.relpath(base)) for i in dirs)
        )]

        if getattr(options, 'entry_point', None):
            text.append('Main-Class: {}'.format(options.entry_point))

        source = File(Path(name + '-manifest.txt'))
        WriteFile(build, source, text)
        options.manifest = source

    def _call(self, cmd, input, output, manifest, libs=None, flags=None):
        return list(chain(
            cmd, iterate(flags), [output, manifest], iterate(input)
        ))

    def transform_input(self, input):
        return ['@' + safe_str.safe_str(i) if isinstance(i, JvmClassList)
                else i for i in input]

    def output_file(self, name, options):
        if getattr(options, 'entry_point', None):
            filetype = ExecutableLibrary
        else:
            filetype = Library
        return filetype(Path(name + '.jar'), self.builder.object_format,
                        self.lang)


class JvmPackageResolver(object):
    def __init__(self, builder, env, command):
        self.builder = builder

        if self.lang == 'scala':
            env_vars = {'JAVA_OPTS': '-XshowSettings:properties'}
            env_vars.update(env.variables)
            args = ['-version']
            returncode = 1
        else:
            env_vars = env.variables
            args = ['-XshowSettings:properties', '-version']
            returncode = 0

        output = shell.execute(
            command + args, env=env_vars, stdout=shell.Mode.devnull,
            stderr=shell.Mode.pipe, returncode=returncode
        )
        self.ext_dirs = self._get_dirs('java.ext.dirs', output)
        self.classpath = self._get_dirs('java.class.path', output)

    @property
    def lang(self):
        return self.builder.lang

    def _get_dirs(self, key, output):
        ex = r'^(\s*){} = (.*(?:\n\1\s+.*)*)'.format(re.escape(key))
        m = re.search(ex, output, re.MULTILINE)
        if not m:
            return []
        return [i.strip() for i in m.group(2).split('\n')]

    def _library(self, name):
        jarname = name + '.jar'
        for base in self.ext_dirs:
            fullpath = os.path.join(base, jarname)
            if os.path.exists(fullpath):
                return Library(Path(fullpath, Root.absolute),
                               self.builder.object_format,
                               external=True)

        for path in self.classpath:
            if os.path.basename(path) == jarname and os.path.exists(path):
                return Library(Path(path, Root.absolute),
                               self.builder.object_format,
                               external=True)

        raise IOError("unable to find library '{}'".format(name))

    def resolve(self, name, version, kind, header, header_only):
        return CommonPackage(name, self.builder.object_format,
                             libs=[self._library(name)])


class JvmRunner(BuildCommand):
    def __init__(self, builder, env, name, command):
        BuildCommand.__init__(self, builder, env, name, name, command)

    def _call(self, cmd, file, jar=False):
        result = list(cmd)
        if jar and self.lang != 'scala':
            result.append('-jar')
        result.append(file)
        return result

    def run_arguments(self, file):
        if isinstance(file, Executable):
            return self(file, jar=True)
        elif isinstance(file, JvmClassList):
            return self(file.object_file)
        elif isinstance(file, ObjectFile):
            return self(file)
        raise TypeError('expected an executable or object file for {} to run'
                        .format(self.lang))
