import os.path
import re

from . import builder, cc, msvc

# XXX: Currently, we tie the linker to a single language, much like the
# compiler. However, linkers can generally take object files made from multiple
# source languages. We should figure out what the correct thing to do here is.

def _builder(env, var, cmd, cc_builder):
    default_cmd = 'cl' if env.platform.name == 'windows' else cmd
    cmd = env.getvar(var, default_cmd)

    if re.search(r'cl(\.exe)?$', cmd):
        origin = os.path.dirname(cmd)
        link_cmd = env.getvar(var + '_LINK', os.path.join(origin, 'link'))
        lib_cmd  = env.getvar(var + '_LIB',  os.path.join(origin, 'lib'))
        return msvc.MsvcBuilder(env, cmd, link_cmd, lib_cmd)
    else:
        return cc_builder(env, cmd, env.getvar('AR', 'ar'))

@builder('c')
def c_builder(env):
    return _builder(env, 'CC', 'cc', cc.CcBuilder)

@builder('c++')
def cxx_builder(env):
    return _builder(env, 'CXX', 'c++', cc.CxxBuilder)
