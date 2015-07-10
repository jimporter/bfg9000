from setuptools import setup, find_packages
from bfg9000.version import __version__

setup(
    name='bfg9000',
    version=__version__,

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    packages=find_packages(exclude=['test']),
    extras_require={'msbuild': ['lxml']},
    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
        ],
        'bfg9000.backends': [
            'make=bfg9000.backends.make:write',
            'ninja=bfg9000.backends.ninja:write',
            'msbuild=bfg9000.backends.msbuild:write [msbuild]',
        ],
    },

    test_suite='test',
)
