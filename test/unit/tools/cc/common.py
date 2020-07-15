from bfg9000.languages import Languages

known_langs = Languages()
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')
with known_langs.make('java') as x:
    x.vars(compiler='JAVAC', flags='JAVAFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if args[-1] == '-Wl,--version':
        return '', ('COLLECT_GCC=g++\n/usr/bin/collect2 --version\n' +
                    '/usr/bin/ld --version\n')
    elif args[-1] == '-print-search-dirs':
        return 'libraries: =/lib/search/dir1:/lib/search/dir2\n'
    elif args[-1] == '-print-sysroot':
        return '/'
    elif args[-1] == '--verbose':
        return 'SEARCH_DIR("/usr")\n'
