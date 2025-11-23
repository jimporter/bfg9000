from bfg9000.languages import Languages

known_langs = Languages()
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')
with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', flags='JAVAFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if '--version' in args:
        if args[0] == '/usr/bin/ld':
            return 'GNU ld (GNU Binutils for Ubuntu) 2.34'
        return ('g++ (Ubuntu 5.4.0-6ubuntu1~16.04.6) 5.4.0 20160609\n' +
                'Copyright (C) 2015 Free Software Foundation, Inc.')
    if '-Wl,--not-a-real-flag' in args:
        return ('COLLECT_GCC=g++\n/usr/bin/collect2 --not-a-real-flag\n' +
                '/usr/bin/ld --not-a-real-flag\n')
    elif '-print-search-dirs' in args:
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif '-print-sysroot' in args:
        return '/'
    elif '--verbose' in args:
        return 'SEARCH_DIR("/usr")\n'
    raise OSError('unknown command: {}'.format(args))
