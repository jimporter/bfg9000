import os
import subprocess
from enum import Enum

from .list import shell_list  # noqa
from ..iterutils import listify
from ..path import Path
from ..platforms import platform_name
from ..safe_str import safe_str

windows_names = ('winnt', 'win9x', 'msdos')

if platform_name() in windows_names:
    from .windows import *  # noqa
else:
    from .posix import *  # noqa

Mode = Enum('Mode', ['normal', 'pipe', 'stdout', 'devnull'])
CalledProcessError = subprocess.CalledProcessError


def which(names, env=os.environ, base_dirs=None, resolve=False,
          kind='executable'):
    paths = env.get('PATH', os.defpath).split(os.pathsep)
    exts = ['']
    if platform_name() in windows_names + ('cygwin',):
        exts.extend(env.get('PATHEXT', '').split(os.pathsep))

    names = listify(names)
    if len(names) == 0:
        raise TypeError('must supply at least one name')

    for name in names:
        name = listify(name)
        check = (name[0].string(base_dirs) if isinstance(name[0], Path)
                 else name[0])
        if os.path.isabs(check):
            fullpaths = [check]
        else:
            search = ['.'] if os.path.dirname(check) else paths
            fullpaths = [os.path.normpath(os.path.join(path, check))
                         for path in search]

        for fullpath in fullpaths:
            for ext in exts:
                withext = fullpath + ext
                if os.path.exists(withext):
                    return [withext] + name[1:] if resolve else name

    raise IOError("unable to find {kind}{filler} {names}".format(
        kind=kind, filler='; tried' if len(names) > 1 else '',
        names=', '.join("{!r}".format(i) for i in names)
    ))


def execute(args, shell=False, env=None, base_dirs=None, stdout=Mode.normal,
            stderr=Mode.normal, returncode=0):
    def stringify(s):
        s = safe_str(s)
        return s.string(base_dirs) if isinstance(s, Path) else s

    if not shell:
        args = [stringify(i) for i in args]

    devnull = (open(os.devnull, 'wb') if Mode.devnull in (stdout, stderr)
               else None)

    def conv(mode):
        return ({Mode.normal : None,
                 Mode.pipe   : subprocess.PIPE,
                 Mode.stdout : subprocess.STDOUT,
                 Mode.devnull: devnull}).get(mode, mode)

    try:
        proc = subprocess.Popen(
            args, universal_newlines=True, shell=shell, env=env,
            stdout=conv(stdout), stderr=conv(stderr)
        )
        output = proc.communicate()
        if ( returncode != 'any' and
             proc.returncode not in listify(returncode) ):
            raise CalledProcessError(proc.returncode, args)

        if stdout == Mode.pipe:
            if stderr == Mode.pipe:
                return output
            return output[0]
        return output[1]
    finally:
        if devnull:
            devnull.close()
