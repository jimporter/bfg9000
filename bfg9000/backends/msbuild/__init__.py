import re
import subprocess

from ...platforms import which

try:
    msbuild = which('msbuild')
    output = subprocess.check_output(
        [msbuild, '/version'],
        universal_newlines=True
    )
    m = re.search(r'([\d\.]+)$', output)
    if m:
        version = m.group(1)
except IOError:
    version = None
