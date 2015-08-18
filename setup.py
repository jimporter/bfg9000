from setuptools import setup, find_packages
from bfg9000.version import version_string

setup(
    name='bfg9000',
    version=version_string,

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    packages=find_packages(exclude=['test']),

    install_requires=['enum-compat'],
    setup_requires=['packaging'],
    extras_require={'msbuild': ['lxml']},

    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
            'depfixer=bfg9000.depfixer:main',
        ],
        'bfg9000.backends': [
            'make=bfg9000.backends.make.rules',
            'ninja=bfg9000.backends.ninja.rules',
            'msbuild=bfg9000.backends.msbuild.rules [msbuild]',
        ],
    },

    test_suite='test',
)
