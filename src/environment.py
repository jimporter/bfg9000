import os.path
import platform

import toolchains.ar
import toolchains.cc
import toolchains.msvc

class UnixPlatform(object):
    def object_file_name(self, basename):
        return basename + '.o'

    def executable_name(self, basename):
        return basename

    def static_library_name(self, basename):
        return 'lib' + basename + '.a'

    def shared_library_name(self, basename):
        return 'lib' + basename + '.so'

class DarwinPlatform(UnixPlatform):
    def shared_library_name(self, basename):
        return 'lib' + basename + '.dylib'

class WindowsPlatform(object):
    def object_file_name(self, basename):
        return basename + '.obj'

    def executable_name(self, basename):
        return basename + '.exe'

    def static_library_name(self, basename):
        return basename + '.lib'

    def shared_library_name(self, basename):
        return basename + '.lib', basename + '.dll'

class Environment(object):
    def __init__(self, bfgpath, srcdir, builddir, backend, install_prefix):
        self.bfgpath = bfgpath
        self.srcdir = srcdir
        self.builddir = builddir
        self.backend = backend
        self.install_prefix = install_prefix

        platforms = {
            'Windows': WindowsPlatform,
            'Darwin': DarwinPlatform
        }
        platform_name = platform.system()
        platform_info = platforms.get(platform_name, UnixPlatform)()

        # TODO: Come up with a more flexible way to initialize the compilers and
        # linkers for each language.
        if platform_name == 'Windows':
            compiler = toolchains.msvc.MSVCCompiler(platform_info)
            exelinker = toolchains.msvc.MSVCLinker(platform_info, 'executable')
            liblinker = toolchains.msvc.MSVCLinker(platform_info,
                                                   'static_library')
            dlllinker = toolchains.msvc.MSVCLinker(platform_info,
                                                   'shared_library')
            self._compilers = {
                'c'  : compiler,
                'c++': compiler,
            }
            self._linkers = {
                'executable': {
                    'c'  : exelinker,
                    'c++': exelinker,
                },
                'static_library': {
                    'c'  : liblinker,
                    'c++': liblinker,
                },
                'shared_library': {
                    'c'  : dlllinker,
                    'c++': dlllinker,
                },
            }
        else:
            self._compilers = {
                'c'  : toolchains.cc.CcCompiler(platform_info),
                'c++': toolchains.cc.CxxCompiler(platform_info),
            }
            self._linkers = {
                'executable': {
                    'c'  : toolchains.cc.CcLinker(platform_info, 'executable'),
                    'c++': toolchains.cc.CxxLinker(platform_info, 'executable'),
                },
                'static_library': {
                    'c'  : toolchains.ar.ArLinker(platform_info),
                    'c++': toolchains.ar.ArLinker(platform_info),
                },
                'shared_library': {
                    'c'  : toolchains.cc.CcLinker(platform_info,
                                                  'shared_library'),
                    'c++': toolchains.cc.CxxLinker(platform_info,
                                                   'shared_library'),
                },
            }

    def compiler(self, lang):
        return self._compilers[lang]

    def linker(self, lang, mode):
        if isinstance(lang, basestring):
            return self._linkers[mode][lang]

        if not isinstance(lang, set):
            lang = set(lang)
        # TODO: Be more intelligent about this when we support more languages
        if 'c++' in lang:
            return self._linkers[mode]['c++']
        return self._linkers[mode]['c']
