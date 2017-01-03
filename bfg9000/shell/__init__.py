import subprocess

from .. import platforms

if platforms.platform_name() == 'windows':
    from .windows import *
else:
    from .posix import *


class shell_list(list):
    """A special subclass of list used to mark that this command line uses
    special shell characters."""
    pass
