import os

import file_types
from path import Path

class NativeCompiler(object):
    def __init__(self, platform):
        self.platform = platform

    def output_file(self, name, lang):
        head, tail = os.path.split(name)
        path = os.path.join(head, self.platform.object_file_name(tail))
        return file_types.ObjectFile(path, Path.builddir, lang)

class NativeLinker(object):
    def __init__(self, platform, mode):
        self.platform = platform
        self.mode = mode

    def output_file(self, name):
        head, tail = os.path.split(name)

        if self.mode == 'executable':
            path = os.path.join(head, self.platform.executable_name(tail))
            return file_types.Executable(path, Path.builddir)
        elif self.mode == 'static_library':
            path = os.path.join(head, self.platform.static_library_name(tail))
            return file_types.StaticLibrary(tail, path, Path.builddir)
        elif self.mode == 'shared_library':
            output = self.platform.shared_library_name(tail)
            if type(output) == tuple:
                types = file_types.SharedLibrary, file_types.DynamicLibrary
                return tuple(t(tail, os.path.join(head, out), Path.builddir)
                             for t, out in zip(types, output))
            else:
                return file_types.SharedLibrary(
                    tail, os.path.join(head, output), Path.builddir
                )
        else:
            raise RuntimeError('unknown mode "{}"'.format(self.mode))
