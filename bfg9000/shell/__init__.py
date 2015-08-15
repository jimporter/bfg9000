from . import posix
from . import windows
from .. import platforms

if platforms.platform_name() == 'windows':
    from .windows import *
else:
    from .posix import *
