import os
import platform
import re
import subprocess
import sys
from setuptools import setup, find_packages, Command

from bfg9000.version import version


class DocServe(Command):
    description = 'serve the documentation locally'
    user_options = [
        ('dev-addr=', None, 'address to host the documentation on'),
    ]

    def initialize_options(self):
        self.dev_addr = '0.0.0.0:8000'

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(['mkdocs', 'serve', '--dev-addr=' + self.dev_addr])


class DocDeploy(Command):
    description = 'push the documentation to GitHub'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(['mkdocs', 'gh-deploy', '--clean'])


custom_cmds = {
    'doc_serve': DocServe,
    'doc_deploy': DocDeploy,
}

try:
    from flake8.main import Flake8Command

    class LintCommand(Flake8Command):
        def distribution_files(self):
            return ['setup.py', 'bfg9000', 'examples', 'test']

    custom_cmds['lint'] = LintCommand
except:
    pass

more_scripts = []
more_requires = []

if os.getenv('NO_DOPPEL') not in ['1', 'true']:
    more_requires.append('doppel')

if sys.version_info < (3, 4):
    more_requires.append('enum34')

platform_name = platform.system()
if platform_name == 'Windows':
    more_scripts.append('bfg9000-setenv=bfg9000.setenv:main')
elif platform_name == 'Linux':
    if os.getenv('NO_PATCHELF') not in ['1', 'true']:
        more_requires.append('patchelf-wrapper')

with open('README.md', 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# bfg9000.*)\n\n(.+\n)*', r'\1', f.read())

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='bfg9000',
    version=version,

    description='A cross-platform build file generator',
    long_description=long_desc,
    keywords='build file generator',
    url='https://jimporter.github.io/bfg9000/',

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    packages=find_packages(exclude=['test', 'test.*']),

    install_requires=(
        ['colorama', 'packaging', 'six'] + more_requires
    ),
    extras_require={
        'deploy': ['pypandoc'],
        'doc': ['mkdocs', 'mkdocs-bootswatch'],
        'lint': ['flake8'],
        'msbuild': ['lxml'],
    },

    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
            '9k=bfg9000.driver:simple_main',
            'bfg9000-depfixer=bfg9000.depfixer:main',
        ] + more_scripts,
        'bfg9000.backends': [
            'make=bfg9000.backends.make.writer',
            'ninja=bfg9000.backends.ninja.writer',
            'msbuild=bfg9000.backends.msbuild.writer [msbuild]',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
