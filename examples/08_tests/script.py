import sys

with open(sys.argv[1]) as f:
    if f.readline().strip() == 'good':
        exit(0)
    exit(1)
