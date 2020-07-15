from bfg9000.languages import Languages

known_langs = Languages()
with known_langs.make('c') as x:
    x.vars(compiler='CC', flags='CFLAGS')
with known_langs.make('c++') as x:
    x.vars(compiler='CXX', flags='CXXFLAGS')


def mock_which(*args, **kwargs):
    return ['command']
