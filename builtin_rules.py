import os

from builtins import builtin
from languages import ext2lang
import node

@builtin
class source_file(node.Node):
    def __init__(self, name, lang=None):
        self.name = name
        self.kind = 'source_file' # TODO: Remove
        self.lang = ext2lang.get( os.path.splitext(name)[1] )
        self.deps = []

@builtin
class object_file(node.Node):
    def __init__(self, name, file, deps=None, options=None, lang=None):
        self.name = name
        self.kind = 'object_file' # TODO: Remove
        self.file = node.blah(file, source_file, lang=lang)
        self.deps = deps or []
        self.options = options

        node.all_targets.append(self) # TODO: Put this somewhere common

    @property
    def lang(self):
        return self.file.lang

@builtin
def object_files(files, lang=None, options=None):
    return [object_file(os.path.splitext(f)[0], file=f, lang=lang,
                        options=options) for f in files]

class any_library(node.Node):
    pass

@builtin
class external_library(any_library):
    def __init__(self, name):
        self.name = name
        self.kind = 'external_library' # TODO: Remove


def _ensure_library(x):
    if isinstance(x, library) or isinstance(x, external_library):
        return x
    else:
        return external_library(x)

class binary(node.Node):
    def __init__(self, name, files, libs=None, lang=None, compile_options=None,
                 link_options=None, deps=None):
        self.name = name
        self.kind = 'binary' # TODO: Remove
        self.files = object_files(files=files, lang=lang,
                                  options=compile_options)
        self.libs = [node.blah(i, any_library, external_library)
                     for i in libs or []]
        self.compile_options = compile_options
        self.link_options = link_options
        self.deps = deps or []

        node.all_targets.append(self) # TODO: Put this somewhere common

@builtin
class executable(binary):
    def __init__(self, *args, **kwargs):
        binary.__init__(self, *args, **kwargs)
        self.kind = 'executable' # TODO: Remove

@builtin
class library(binary, any_library):
    def __init__(self, *args, **kwargs):
        binary.__init__(self, *args, **kwargs)
        self.kind = 'library' # TODO: Remove

@builtin
class alias(node.Node):
    def __init__(self, name, deps=None):
        self.name = name
        self.kind = 'alias' # TODO: Remove
        self.deps = deps or []

        node.all_targets.append(self) # TODO: Put this somewhere common

@builtin
class command(node.Node):
    def __init__(self, name, cmd, deps=None):
        self.name = name
        self.kind = 'command' # TODO: Remove
        self.cmd = cmd
        self.deps = deps or []

        node.all_targets.append(self) # TODO: Put this somewhere common
