import re
import subprocess

from ...platforms import which

version = None
try:
    make = which(['make', 'gmake'])
    output = subprocess.check_output([make, '--version'])
    m = re.match(r'GNU Make ([\d\.]+)', output)
    if m:
        version = m.group(1)
except IOError:
    pass
