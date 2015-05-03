import os.path
import platform

import toolchains.ar
import toolchains.cc

class UnixPlatform(object):
    def object_file_name(self, basename):
        return basename + '.o'

    def executable_name(self, basename):
        return basename

    def shared_library_name(self, basename):
        return 'lib' + basename + '.so'

    def static_library_name(self, basename):
        return 'lib' + basename + '.a'

    import_library_name = shared_library_name

class DarwinPlatform(UnixPlatform):
    def shared_library_name(self, basename):
        return 'lib' + basename + '.dylib'

class WindowsPlatform(object):
    def object_file_name(self, basename):
        return basename + '.obj'

    def executable_name(self, basename):
        return basename + '.exe'

    def shared_library_name(self, basename):
        return basename + '.dll'

    def static_library_name(self, basename):
        return basename + '.lib'

    import_library_name = static_library_name

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
        platform_info = platforms.get(platform.system(), UnixPlatform)()

        self._compilers = {
            'c'  : toolchains.cc.CcCompiler(platform_info),
            'c++': toolchains.cc.CxxCompiler(platform_info),
        }
        self._linkers = {
            'executable': {
                'c'  : toolchains.cc.CcLinker('executable', platform_info),
                'c++': toolchains.cc.CxxLinker('executable', platform_info),
            },
            'shared_library': {
                'c'  : toolchains.cc.CcLinker('shared_library', platform_info),
                'c++': toolchains.cc.CxxLinker('shared_library', platform_info),
            },
            'static_library': {
                'c'  : toolchains.ar.ArLinker(platform_info),
                'c++': toolchains.ar.ArLinker(platform_info),
            }
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
