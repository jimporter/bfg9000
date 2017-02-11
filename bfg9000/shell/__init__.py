import os
import subprocess

from ..platform_name import platform_name

if platform_name() == 'windows':
    from .windows import *
else:
    from .posix import *


class shell_list(list):
    """A special subclass of list used to mark that this command line uses
    special shell characters."""
    pass


def execute(args, shell=False, env=None, quiet=False):
    stderr = open(os.devnull, 'wb') if quiet else None
    try:
        return subprocess.check_output(
            args, universal_newlines=True, shell=shell, env=env, stderr=stderr
        )
    finally:
        if stderr:
            stderr.close()
