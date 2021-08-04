import re
from itertools import chain

from ... import options as opts, safe_str
from ..common import BuildCommand, library_macro, SimpleBuildCommand
from ...arguments.windows import ArgumentParser
from ...file_types import DllBinary, Executable, StaticLibrary, WholeArchive
from ...iterutils import iterate, merge_into_dict, uniques
from ...objutils import memoize
from ...packages import Framework
from ...path import Path
from ...versioning import SpecifierSet


class MsvcLinker(BuildCommand):
    __lib_re = re.compile(r'(.*)\.lib$')
    __known_langs = {'c', 'c++'}
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++'},
    }

    _always_libs = [
        'kernel32', 'user32', 'gdi32', 'winspool', 'comdlg32', 'advapi32',
        'shell32', 'ole32', 'oleaut32', 'uuid', 'odbc32', 'odbccp32',
    ]

    def _extract_lib_name(self, library):
        lib = library if isinstance(library, str) else library.path.basename()
        m = self.__lib_re.match(lib)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(lib))
        return m.group(1)

    def can_link(self, format, langs):
        if format != self.builder.object_format:
            return False
        relevant_langs = self.__known_langs.intersection(langs)
        return self.__allowed_langs[self.lang].issuperset(relevant_langs)

    @property
    def needs_libs(self):
        return True

    @property
    def needs_package_options(self):
        return True

    def search_dirs(self, strict=False):
        lib_path = self.env.variables.getpaths('LIBRARY_PATH')
        lib = self.env.variables.getpaths('LIB')
        return lib_path + lib

    def _call(self, cmd, input, output, libs=None, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), iterate(input),
            iterate(libs), ['/OUT:' + output]
        ))

    @property
    def _always_flags(self):
        return ['/nologo']

    def always_libs(self, primary):
        if not primary:
            return opts.option_list()
        return opts.option_list(opts.lib(i + '.lib')
                                for i in self._always_libs)

    def _link_lib(self, library, syntax):
        if isinstance(library, Framework):
            raise TypeError('MSVC does not support frameworks')
        elif isinstance(library, WholeArchive):
            if not self.version or self.version in SpecifierSet('>=19'):
                return ['/WHOLEARCHIVE:' + library.path]
            raise TypeError('whole-archives require MSVC 2015 Update 2')

        if syntax == 'cc':
            return ['-l' + self._extract_lib_name(library)]
        else:
            # Pass the raw path to the library. We do this to avoid adding more
            # `/LIBPATH` options than we really need, which makes it easier to
            # find the right library when there are name collisions (e.g.
            # linking to a system `libfoo` when also building a local `libfoo`
            # to use elsewhere).
            return [library if isinstance(library, str) else library.path]

    def _lib_dir(self, library, syntax):
        if syntax == 'cc' and not isinstance(library, WholeArchive):
            return [library.path.parent()]
        return []

    def flags(self, options, global_options=None, output=None, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        flags, lib_dirs = [], []
        auto_entry_point = None
        for i in options:
            if isinstance(i, opts.lib_dir):
                lib_dirs.append(i.directory.path)
            elif isinstance(i, opts.lib):
                lib_dirs.extend(self._lib_dir(i.library, syntax))
            elif isinstance(i, opts.module_def):
                flags.append('/DEF:' + i.value.path)
            elif isinstance(i, opts.debug):
                flags.append('/DEBUG')
            elif isinstance(i, opts.static):
                pass
            elif isinstance(i, opts.optimize):
                if opts.OptimizeValue.linktime in i.value:
                    flags.append('/LTCG')
            elif isinstance(i, opts.entry_point):
                auto_entry_point = False
                flags.append('/ENTRY:{}'.format(i.value))
            elif isinstance(i, opts.gui):
                flags.append('/SUBSYSTEM:WINDOWS')
                if i.main and auto_entry_point is not False:
                    auto_entry_point = True
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            elif isinstance(i, opts.lib_literal):
                pass
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))

        if auto_entry_point:
            flags.append('/ENTRY:mainCRTStartup')
        prefix = '-L' if syntax == 'cc' else '/LIBPATH:'
        flags.extend(prefix + i for i in uniques(lib_dirs))
        return flags

    def lib_flags(self, options, global_options=None, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        flags = []
        for i in options:
            if isinstance(i, opts.lib):
                flags.extend(self._link_lib(i.library, syntax))
            elif isinstance(i, opts.lib_literal):
                flags.append(i.value)
        return flags

    @staticmethod
    @memoize
    def __parser():
        parser = ArgumentParser(case_sensitive=False)
        parser.add('/nologo')
        parser.add('/debug')
        parser.add('/libpath', type=list, dest='libdirs')
        return parser

    @staticmethod
    @memoize
    def __lib_parser():
        parser = ArgumentParser(case_sensitive=False)
        parser.add('/nologo')
        parser.add_unnamed('libs')
        return parser

    def parse_flags(self, flags, lib_flags):
        result, extra = self.__parser().parse_known(flags)
        libresult, libextra = self.__lib_parser().parse_known(lib_flags)

        merge_into_dict(result, libresult)
        result['extra'] = extra + libextra
        return result


class MsvcExecutableLinker(MsvcLinker):
    def __init__(self, builder, env, name, *, command, flags, libs):
        super().__init__(builder, env, name + '_link', command=command,
                         flags=flags, libs=libs)

    def output_file(self, name, step):
        path = Path(name + self.env.target_platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class MsvcSharedLibraryLinker(MsvcLinker):
    def __init__(self, builder, env, name, *, command, flags, libs):
        super().__init__(builder, env, name + '_linklib',
                         command=command, flags=flags, libs=libs)

    @property
    def num_outputs(self):
        return 2

    def _call(self, cmd, input, output, libs=None, flags=None):
        result = super()._call(cmd, input, output[0], libs, flags)
        result.append('/IMPLIB:' + output[1])
        return result

    @property
    def _always_flags(self):
        return super()._always_flags + ['/DLL']

    def compile_options(self, step):
        return opts.option_list(
            opts.define(library_macro(step.name, 'shared_library'))
        )

    def output_file(self, name, step):
        dllname = Path(name + self.env.target_platform.shared_library_ext)
        impname = Path(name + '.lib')
        expname = Path(name + '.exp')
        dll = DllBinary(dllname, self.builder.object_format, self.lang,
                        impname, expname)
        return [dll, dll.import_lib, dll.export_file]


class MsvcStaticLinker(SimpleBuildCommand):
    def can_link(self, format, langs):
        return format == self.builder.object_format

    def _call(self, cmd, input, output, flags=None):
        return list(chain(
            cmd, iterate(flags), iterate(input), ['/OUT:' + output]
        ))

    def compile_options(self, step):
        return self.forwarded_compile_options(step)

    def forwarded_compile_options(self, step):
        return opts.option_list(
            opts.define(library_macro(step.name, 'static_library'))
        )

    def flags(self, options, global_options=None, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags

    def output_file(self, name, step):
        return StaticLibrary(Path(name + '.lib'), self.builder.object_format,
                             step.input_langs)

    def parse_flags(self, flags):
        return {'extra': flags}
