import subprocess
from setuptools import setup, find_packages, Command
from bfg9000.version import version

class doc_serve(Command):
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

class doc_deploy(Command):
    description = 'push the documentation to GitHub'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(['mkdocs', 'gh-deploy', '--clean'])

setup(
    name='bfg9000',
    version=version,

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    packages=find_packages(exclude=['test']),

    install_requires=['enum-compat', 'packaging'],
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

    cmdclass={
        'doc_serve': doc_serve,
        'doc_deploy': doc_deploy,
    },
)
