import sys
from shlex import split

if sys.hexversion >= 0x030300F0:
    from shlex import quote
else:
    from pipes import quote
