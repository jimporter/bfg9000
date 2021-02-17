from bfg9000.languages import Languages

known_langs = Languages()
with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')


def mock_which(*args, **kwargs):
    return ['command']


def mock_execute(args, **kwargs):
    if '-?' in args:
        return ('Microsoft (R) C/C++ Optimizing Compiler Version ' +
                '19.12.25831 for x86')
    raise OSError('unknown command: {}'.format(args))
