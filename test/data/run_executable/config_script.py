import os.path
import sys

with open(os.path.join(sys.argv[1], 'file.txt'), 'w') as f:
    f.write('hello\n')
