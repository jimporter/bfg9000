import re

from .. import shell
from ..versioning import detect_version


class LdLinker(object):
    def __init__(self, builder, env, command, version_output):
        self.builder = builder
        self.env = env
        self.command = command

        if 'GNU ld' in version_output:
            self.brand = 'bfd'
            self.version = detect_version(version_output)
        elif 'GNU gold' in version_output:
            self.brand = 'gold'
            self.version = detect_version(version_output, post='$',
                                          flags=re.MULTILINE)
        else:
            self.brand = 'unknown'
            self.version = None

    @property
    def lang(self):
        return self.builder.lang

    @property
    def flavor(self):
        return 'ld'

    def search_dirs(self, sysroot='/', strict=False):
        try:
            output = self.env.execute(
                self.command + ['--verbose'], stdout=shell.Mode.pipe,
                stderr=shell.Mode.devnull
            )
            search_dirs = [i.group(1) for i in re.finditer(
                r'SEARCH_DIR\("((?:[^"\\]|\\.)*)"\)', output)
            ]
            return [sysroot.rstrip('/') + i[1:] if i[0] == '=' else i
                    for i in search_dirs]
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            return []
