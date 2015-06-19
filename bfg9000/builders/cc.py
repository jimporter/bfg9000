import os
import re

from .. import shell
from .. import utils
from ..file_types import *

class CcCompilerBase(object):
    def __init__(self, platform, command, name):
        self.platform = platform
        self.command_name = command
        self.name = name
        self.command_var = name

    def command(self, cmd, input, output, deps=None, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.extend(['-c', input])
        if deps:
            result.extend(['-MMD', '-MF', deps])
        result.extend(['-o', output])
        return result

    def output_file(self, name, lang):
        return ObjectFile(name + '.o', Path.builddir, lang)

    @property
    def deps_flavor(self):
        return 'gcc'

    @property
    def library_args(self):
        return ['-fPIC']

    def include_dir(self, directory):
        return ['-I' + directory.path.local_path()]

class CcLinkerBase(object):
    def __init__(self, platform, mode, command, name):
        self.platform = platform
        self.mode = mode
        self.command_name = command
        self.name = 'link_' + name
        self.command_var = name
        self.link_var = 'ld'

        # Create a regular expression to extract the library name for linking
        # with -l. TODO: Support .lib as an extension on Windows/Cygwin?
        exts = [r'\.a']
        if not self.platform.has_import_library:
            exts.append(re.escape(self.platform.shared_library_ext))
        self._lib_re = re.compile('lib(.*)(?:' + '|'.join(exts) + ')$')

    def command(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.extend(utils.iterate(input))
        result.extend(utils.iterate(libs))
        result.extend(['-o', output])
        return result

    def output_file(self, name):
        if self.mode == 'executable':
            return Executable(
                name + self.platform.executable_ext, Path.builddir
            )
        elif self.mode == 'shared_library':
            head, tail = os.path.split(name)
            def libpath(prefix='lib'):
                return os.path.join(
                    head, 'lib' + tail + self.platform.shared_library_ext
                )

            if self.platform.has_import_library:
                dllprefix = 'cyg' if self.platform.name == 'cygwin' else 'lib'
                return (
                    DynamicLibrary(libpath(dllprefix), Path.builddir),
                    SharedLibrary(libpath() + '.a', Path.builddir),
                )
            else:
                return SharedLibrary(libpath(), Path.builddir)
        else:
            raise ValueError('unknown mode {}'.format(repr(self.mode)))

    @property
    def mode_args(self):
        return ['-shared', '-fPIC'] if self.mode == 'shared_library' else []

    def lib_dirs(self, libraries):
        dirs = utils.uniques(i.path.parent().local_path() for i in libraries)
        return ['-L' + i for i in dirs]

    def link_lib(self, library):
        lib_name = library.path.basename()
        if not isinstance(library, ExternalLibrary):
            m = self._lib_re.match(lib_name)
            if not m:
                raise ValueError("{} is not a valid library"
                                 .format(repr(lib_name)))
            lib_name = m.group(1)
        return ['-l' + lib_name]

    def import_lib(self, library):
        if self.platform.has_import_library:
            raise ValueError("platform {} doesn't have import libraries"
                             .format(repr(self.platform.name)))
        if self.mode != 'shared_library':
            raise ValueError('import libraries only apply to shared libraries')
        return ['-Wl,--out-implib=' + library.path.local_path()]

    def rpath(self, paths):
        if not self.platform.has_rpath:
            return []
        rpath = ':'.join(os.path.join('$ORIGIN', i) for i in paths)
        if not rpath:
            return []
        return ['-Wl,-rpath={}'.format(rpath)]

class CcCompiler(CcCompilerBase):
    def __init__(self, platform):
        CcCompilerBase.__init__(self, platform, os.getenv('CC', 'cc'), 'cc')
        self.global_args = (
            shell.split(os.getenv('CFLAGS', '')) +
            shell.split(os.getenv('CPPFLAGS', ''))
        )

class CxxCompiler(CcCompilerBase):
    def __init__(self, platform):
        CcCompilerBase.__init__(self, platform, os.getenv('CXX', 'c++'), 'cxx')
        self.global_args = (
            shell.split(os.getenv('CXXFLAGS', '')) +
            shell.split(os.getenv('CPPFLAGS', ''))
        )

class CcLinker(CcLinkerBase):
    def __init__(self, platform, mode):
        CcLinkerBase.__init__(self, platform, mode, os.getenv('CC', 'cc'), 'cc')
        self.global_args = shell.split(os.getenv('LDFLAGS', ''))
        self.global_libs = shell.split(os.getenv('LDLIBS', ''))

class CxxLinker(CcLinkerBase):
    def __init__(self, platform, mode):
        CcLinkerBase.__init__(
            self, platform, mode, os.getenv('CXX', 'c++'), 'cxx'
        )
        self.global_args = shell.split(os.getenv('LDFLAGS', ''))
        self.global_libs = shell.split(os.getenv('LDLIBS', ''))
