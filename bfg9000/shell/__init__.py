import os
import subprocess
from enum import Enum

from ..platforms import platform_name

if platform_name() == 'windows':
    from .windows import *
else:
    from .posix import *

Mode = Enum('Mode', ['pipe', 'stdout', 'devnull', 'normal'])


class shell_list(list):
    """A special subclass of list used to mark that this command line uses
    special shell characters."""
    pass


def execute(args, shell=False, env=None, stdout=Mode.pipe, stderr=Mode.normal):
    devnull = (open(os.devnull, 'wb') if Mode.devnull in (stdout, stderr)
               else None)

    def conv(mode):
        return ({Mode.pipe:    subprocess.PIPE,
                 Mode.stdout:  subprocess.STDOUT,
                 Mode.devnull: devnull,
                 Mode.normal:  None}).get(mode, mode)

    try:
        proc = subprocess.Popen(
            args, universal_newlines=True, shell=shell, env=env,
            stdout=conv(stdout), stderr=conv(stderr)
        )
        output = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, args)

        if stdout == Mode.pipe:
            if stderr == Mode.pipe:
                return output
            return output[0]
        return output[1]
    finally:
        if devnull:
            devnull.close()
