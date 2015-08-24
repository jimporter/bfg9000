from . import builder, cc, msvc

# XXX: Currently, we tie the linker to a single language, much like the
# compiler. However, linkers can generally take object files made from multiple
# source languages. We should figure out what the correct thing to do here is.

@builder('c')
def c_builder(env):
    if env.platform.name == 'windows':
        return msvc.MsvcBuilder(env)
    else:
        return cc.CcBuilder(env)

@builder('c++')
def cxx_builder(env):
    if env.platform.name == 'windows':
        return msvc.MsvcBuilder(env)
    else:
        return cc.CxxBuilder(env)
