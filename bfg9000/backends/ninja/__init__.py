import subprocess

from ...platforms import which

try:
    ninja = which(['ninja', 'ninja-build'])
    output = subprocess.check_output([ninja, '--version'])
    version = output.strip()
except IOError:
    version = None
