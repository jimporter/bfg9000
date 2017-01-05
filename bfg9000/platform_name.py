import platform
import subprocess


def platform_name():
    name = platform.system().lower()
    if name == 'windows':
        try:
            uname = subprocess.check_output(
                'uname', universal_newlines=True
            ).lower()
            if uname.startswith('cygwin'):
                name = 'cygwin'
        except WindowsError:
            pass
    return name
