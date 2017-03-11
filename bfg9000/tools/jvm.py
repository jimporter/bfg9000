import os
import re

from .common import Command
from .. import safe_str
from .. import shell
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Path, Root


class JvmBuilder(object):
    def __init__(self, env, lang, run_name, run_command, name, command,
                 jar_command, flags_name, flags):
        self.brand = 'jvm'  # XXX: Be more specific?
        self.object_format = 'jvm'

        self.compiler = JvmCompiler(env, lang, name, command, flags_name,
                                    flags)

        linker = JarMaker(env, lang, jar_command)
        self._linkers = {
            'executable': linker,
            'shared_library': linker,
        }
        self.packages = JvmPackageResolver(env, lang, run_command)
        self.runner = JvmRunner(env, lang, run_name, run_command)

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
        return self._linkers[mode]


class JvmCompiler(Command):
    def __init__(self, env, lang, name, command, flags_name, flags):
        Command.__init__(self, env, command)
        self.lang = lang

        self.rule_name = self.command_var = name

        self.flags_var = flags_name
        self.global_args = flags

    @property
    def deps_flavor(self):
        return None

    @property
    def depends_on_libs(self):
        return True

    @property
    def accepts_pch(self):
        return False

    def _call(self, cmd, input, output, args=None):
        jvmoutput = self.env.tool('jvmoutput')

        result = [cmd]
        result.extend(iterate(args))
        result.extend(self._always_args)
        result.append(input)
        return jvmoutput(output, result)

    @property
    def _always_args(self):
        return ['-verbose', '-d', '.']

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
        return JvmClassList(ObjectFile(
            Path(name + '.classlist'), 'jvm', self.lang
        ))


class JarMaker(Command):
    rule_name = command_var = 'jar'
    flags_var = 'jarflags'

    def __init__(self, env, lang, command):
        Command.__init__(self, env, command)
        self.lang = lang

        self.global_args = shell.split(env.getvar('JARFLAGS', 'cfm'))
        self.global_libs = []

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

    def _call(self, cmd, input, output, manifest, libs=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend([output, manifest])
        result.extend(iterate(input))
        return result

    def transform_input(self, input):
        return ['@' + safe_str.safe_str(i) if isinstance(i, JvmClassList)
                else i for i in input]

    def output_file(self, name, options):
        if getattr(options, 'entry_point', None):
            filetype = ExecutableLibrary
        else:
            filetype = Library
        return filetype(Path(name + '.jar'), 'jvm', self.lang)


class JvmPackageResolver(object):
    def __init__(self, env, lang, command):
        if lang == 'scala':
            env_vars = {'JAVA_OPTS': '-XshowSettings:properties'}
            env_vars.update(env.variables)
            cmd = '{} -version'
            returncode = 1
        else:
            env_vars = env.variables
            cmd = '{} -XshowSettings:properties -version'
            returncode = 0

        output = shell.execute(
            cmd.format(command), shell=True, env=env_vars,
            stdout=shell.Mode.devnull, stderr=shell.Mode.pipe,
            returncode=returncode
        )
        self.ext_dirs = self._get_dirs('java.ext.dirs', output)
        self.classpath = self._get_dirs('java.class.path', output)

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
                return Library(Path(fullpath, Root.absolute), 'jvm',
                               external=True)

        for path in self.classpath:
            if os.path.basename(path) == jarname and os.path.exists(path):
                return Library(Path(path, Root.absolute), 'jvm',
                               external=True)

        raise IOError("unable to find library '{}'".format(name))

    def resolve(self, name, version, kind, header, header_only):
        return CommonPackage(name, 'jvm', libs=[self._library(name)])


class JvmRunner(Command):
    def __init__(self, env, lang, rule_name, command):
        Command.__init__(self, env, command)
        self.lang = lang
        self.rule_name = self.command_var = rule_name

    def _call(self, cmd, file, jar=False):
        result = [cmd]
        if jar and self.lang != 'scala':
            result.append('-jar')
        result.append(file)
        return result
