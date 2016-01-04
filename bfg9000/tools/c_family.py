import os.path
import re

from . import builder, ar, cc, msvc
from .. import shell

# XXX: Currently, we tie the linker to a single language, much like the
# compiler. However, linkers can generally take object files made from multiple
# source languages. We should figure out what the correct thing to do here is.


@builder('c', 'c++')
class CFamilyBuilder(object):
    __langs = {
        'c'  : ('CC' , 'cc' ),
        'c++': ('CXX', 'c++'),
    }

    def __init__(self, env, lang):
        self.linkers = {}

        var, default_cmd = self.__langs[lang]
        low_var = var.lower()
        if env.platform.name == 'windows':
            default_cmd = 'cl'
        cmd = env.getvar(var, default_cmd)

        cflags = (
            shell.split(env.getvar(var + 'FLAGS', '')) +
            shell.split(env.getvar('CPPFLAGS', ''))
        )
        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))

        if re.search(r'cl(\.exe)?$', cmd):
            origin = os.path.dirname(cmd)
            link_cmd = env.getvar(var + '_LINK', os.path.join(origin, 'link'))
            lib_cmd = env.getvar(var + '_LIB', os.path.join(origin, 'lib'))

            self.compiler = msvc.MsvcCompiler(env, lang, low_var, cmd, cflags)
            for mode in ['executable', 'shared_library']:
                self.linkers[mode] = msvc.MsvcLinker(
                    env, mode, lang, low_var, link_cmd, ldflags, ldlibs
                )
            self.linkers['static_library'] = msvc.MsvcStaticLinker(
                env, lang, low_var, lib_cmd
            )
        else:
            self.compiler = cc.CcCompiler(env, lang, low_var, cmd, cflags)
            for mode in ['executable', 'shared_library']:
                self.linkers[mode] = cc.CcLinker(
                    env, mode, lang, low_var, cmd, ldflags, ldlibs
                )
            self.linkers['static_library'] = ar.ArLinker(env, lang)
