import sys
from shlex import split

if sys.hexversion >= 0x030300F0:
    from shlex import quote
else:
    from pipes import quote

# TODO: Provide a way for split() to note that shell characters (like | or &&)
# shouldn't be quoted by quote().
