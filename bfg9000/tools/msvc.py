import os.path
from itertools import chain

from .winargparse import ArgumentParser
from .. import shell
from ..builtins.write_file import WriteFile
from ..file_types import *
from ..iterutils import iterate, uniques
from ..languages import lang2src
from ..path import Path, Root


class MsvcBuilder(object):
    def __init__(self, env, lang, name, command, link_command, lib_command,
                 cflags, ldflags, ldlibs):
        self.compiler = MsvcCompiler(env, lang, name, command, cflags)
        self.pch_compiler = MsvcPchCompiler(env, lang, name, command, cflags)
        self._linkers = {
            'executable': MsvcExecutableLinker(
                env, lang, name, link_command, ldflags, ldlibs
            ),
            'shared_library': MsvcSharedLibraryLinker(
                env, lang, name, link_command, ldflags, ldlibs
            ),
            'static_library': MsvcStaticLinker(
                env, lang, name, lib_command
            ),
        }
        self.packages = MsvcPackageResolver(env, lang)

    @property
    def brand(self):
        # XXX: Detect clang-cl.
        return 'msvc'

    @property
    def flavor(self):
        return 'msvc'

    @property
    def auto_link(self):
        return True

    def linker(self, mode):
        return self._linkers[mode]


class MsvcBaseCompiler(object):
    def __init__(self, env, lang, rule_name, command_var, command, cflags):
        self.platform = env.platform
        self.lang = lang

        self.rule_name = rule_name
        self.command_var = command_var
        self.command = command

        self.global_args = ['/nologo'] + cflags

    @property
    def flavor(self):
        return 'msvc'

    @property
    def deps_flavor(self):
        return 'msvc'

    @property
    def num_outputs(self):
        return 1

    @property
    def depends_on_libs(self):
        return False

    def __call__(self, cmd, input, output, deps=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input])
        result.append('/Fo' + output)
        return result

    def _include_dir(self, directory):
        return ['/I' + directory.path]

    def _include_pch(self, pch):
        return ['/Yu' + pch.header_name]

    def args(self, options, output, pkg=False):
        includes = getattr(options, 'includes', [])
        pch = getattr(options, 'pch', None)
        return sum((self._include_dir(i) for i in includes),
                   self._include_pch(pch) if pch else [])

    def link_args(self, mode, defines):
        return ['/D' + i for i in defines]

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add('/D', '-D', type=list, dest='defines')
        parser.add('/I', '-I', type=list, dest='includes')

        warn = parser.add('/W', type=dict, dest='warnings')
        warn.add('0', '1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='as_error')
        warn.add('X-', type=bool, dest='as_error', value=False)

        pch = parser.add('/Y', type=dict, dest='pch')
        pch.add('u', type=str, dest='use')
        pch.add('c', type=str, dest='create')

        result, extra = parser.parse_known(args)
        result['extra'] = extra
        return result


class MsvcCompiler(MsvcBaseCompiler):
    def __init__(self, env, lang, name, command, cflags):
        MsvcBaseCompiler.__init__(self, env, lang, name, name, command, cflags)

    def output_file(self, name, options):
        output = ObjectFile(Path(name + '.obj'), self.platform.object_format,
                            self.lang)
        if options.pch:
            output.extra_objects = [options.pch.object_file]
        return output


class MsvcPchCompiler(MsvcBaseCompiler):
    def __init__(self, env, lang, name, command, cflags):
        MsvcBaseCompiler.__init__(self, env, lang, name + '_pch', name,
                                  command, cflags)

    @property
    def num_outputs(self):
        return 2

    def __call__(self, cmd, input, output, deps=None, args=None):
        result = MsvcBaseCompiler.__call__(self, cmd, input, output[1], deps,
                                           args)
        result.append('/Fp' + output[0])
        return result

    def pre_build(self, build, options, name):
        if options.pch_source is None:
            header = getattr(options, 'file', None)
            ext = lang2src[header.lang][0]
            options.pch_source = SourceFile(header.path.stripext(ext).reroot(),
                                            header.lang)
            options.inject_include_dir = True

            text = '#include "{}"'.format(header.path.basename())
            WriteFile(build, options.pch_source, text)

    def _create_pch(self, header):
        return ['/Yc' + header.path.suffix]

    def args(self, options, output):
        header = getattr(options, 'file', None)
        args = []
        if getattr(options, 'inject_include_dir', False):
            # Add the include path for the generated header; see pre_build()
            # above for more details.
            d = Directory(header.path.parent(), None)
            args.extend(self._include_dir(d))

        args.extend(MsvcBaseCompiler.args(self, options, output) +
                    (self._create_pch(header) if header else []))
        return args

    def output_file(self, name, options):
        pchpath = Path(name).stripext('.pch')
        objpath = options.pch_source.path.stripext('.obj').reroot()
        output = MsvcPrecompiledHeader(
            pchpath, objpath, name, self.platform.object_format, self.lang
        )
        if options.pch:
            output.extra_objects = [options.pch.object_file]
        return [output, output.object_file]


class MsvcLinker(object):
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++'},
    }

    def __init__(self, env, lang, rule_name, command_var, command, ldflags,
                 ldlibs):
        self.platform = env.platform
        self.lang = lang

        self.rule_name = rule_name
        self.command_var = command_var
        self.command = command
        self.link_var = 'ld'

        self.global_args = ['/nologo'] + ldflags
        self.global_libs = ldlibs

    @property
    def flavor(self):
        return 'msvc'

    def can_link(self, format, langs):
        return (format == self.platform.object_format and
                self.__allowed_langs[self.lang].issuperset(langs))

    @property
    def num_outputs(self):
        return 1

    def __call__(self, cmd, input, output, libs=None, args=None):
        result = [cmd] + self._always_args
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.extend(iterate(libs))
        result.append('/OUT:' + output)
        return result

    @property
    def _always_args(self):
        return []

    def _lib_dirs(self, libraries, extra_dirs):
        dirs = uniques(chain(
            (i.path.parent() for i in iterate(libraries)),
            extra_dirs
        ))
        return ['/LIBPATH:' + i for i in dirs]

    def args(self, options, output, pkg=False):
        libraries = getattr(options, 'all_libs', [])
        lib_dirs = getattr(options, 'lib_dirs', [])
        return self._lib_dirs(libraries, lib_dirs)

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add('/nologo')

        result, extra = parser.parse_known(args)
        result['extra'] = extra
        return result

    def _link_lib(self, library):
        if isinstance(library, WholeArchive):
            raise ValueError('MSVC does not support whole-archives')
        return [library.path.basename()]

    def always_libs(self, primary):
        return []

    def libs(self, options, output, pkg=False):
        libraries = getattr(options, 'all_libs', [])
        return sum((self._link_lib(i) for i in libraries), [])


class MsvcExecutableLinker(MsvcLinker):
    def __init__(self, env, lang, name, command, ldflags, ldlibs):
        MsvcLinker.__init__(self, env, lang, name + '_link', name + '_link',
                            command, ldflags, ldlibs)

    def output_file(self, name, options):
        path = Path(name + self.platform.executable_ext)
        return Executable(path, self.platform.object_format)


class MsvcSharedLibraryLinker(MsvcLinker):
    def __init__(self, env, lang, name, command, ldflags, ldlibs):
        MsvcLinker.__init__(self, env, lang, name + '_linklib', name + '_link',
                            command, ldflags, ldlibs)

    @property
    def num_outputs(self):
        return 2

    def __call__(self, cmd, input, output, libs=None, args=None):
        result = MsvcLinker.__call__(self, cmd, input, output[0], libs, args)
        result.append('/IMPLIB:' + output[1])
        return result

    def output_file(self, name, options):
        dllname = Path(name + self.platform.shared_library_ext)
        impname = Path(name + '.lib')
        expname = Path(name + '.exp')
        dll = DllLibrary(dllname, self.platform.object_format, impname,
                         expname)
        return [dll, dll.import_lib, dll.export_file]

    @property
    def _always_args(self):
        return ['/DLL']


class MsvcStaticLinker(object):
    link_var = 'lib'

    def __init__(self, env, lang, name, command):
        self.platform = env.platform
        self.lang = lang

        self.rule_name = self.command_var = name + '_lib'
        self.command = command

        self.global_args = shell.split(env.getvar('LIBFLAGS', ''))

    @property
    def flavor(self):
        return 'msvc'

    def can_link(self, format, langs):
        return format == self.platform.object_format

    def __call__(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name, options):
        return StaticLibrary(Path(name + '.lib'), self.platform.object_format,
                             options.langs)

    def parse_args(self, args):
        return {'other': args}


class MsvcPackageResolver(object):
    def __init__(self, env, lang):
        value = env.getvar('CPATH')
        user_include_dirs = value.split(os.pathsep) if value else []

        value = env.getvar('INCLUDE')
        system_include_dirs = value.split(os.pathsep) if value else []

        self.include_dirs = [i for i in uniques(chain(
            user_include_dirs, system_include_dirs, env.platform.include_dirs
        )) if os.path.exists(i)]

        value = env.getvar('LIB')
        system_lib_dirs = value.split(os.pathsep) if value else []

        value = env.getvar('LIBRARY_PATH')
        user_lib_dirs = value.split(os.pathsep) if value else []

        all_lib_dirs = ( os.path.abspath(i) for i in
                         chain(user_lib_dirs, system_lib_dirs) )
        self.lib_dirs = [i for i in uniques(chain(
            all_lib_dirs, env.platform.lib_dirs
        )) if os.path.exists(i)]

        self.lang = lang
        self.platform = env.platform

    def header(self, name, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.include_dirs

        for base in search_dirs:
            if os.path.exists(os.path.join(base, name)):
                return HeaderDirectory(Path(base, Root.absolute), None,
                                       system=True, external=True)

        raise IOError("unable to find header '{}'".format(name))

    def library(self, name, kind='any', search_dirs=None):
        if search_dirs is None:
            search_dirs = self.lib_dirs
        libname = name + '.lib'

        for base in search_dirs:
            fullpath = os.path.join(base, libname)
            if os.path.exists(fullpath):
                # We don't actually know what kind of library this is. It could
                # be a static library or an import library (which we classify
                # as a kind of shared lib).
                return Library(Path(fullpath, Root.absolute),
                               self.platform.object_format, external=True)
        raise IOError("unable to find library '{}'".format(name))
