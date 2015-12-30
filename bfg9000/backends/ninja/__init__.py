from packaging.version import Version
import subprocess

from ...platforms import which

try:
    ninja = which(['ninja', 'ninja-build'])
    output = subprocess.check_output(
        [ninja, '--version'],
        universal_newlines=True
    )
    version = Version(output.strip())
except IOError:
    version = None
