from pkg_resources import parse_version
import subprocess

from ...platforms import which

try:
    ninja = which(['ninja', 'ninja-build'])
    output = subprocess.check_output([ninja, '--version'])
    version = parse_version(output.strip())
except IOError:
    version = None
