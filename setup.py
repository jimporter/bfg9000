import platform
import re
import subprocess
from setuptools import setup, find_packages, Command
from bfg9000.version import version

platform_name = platform.system()


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

extra_scripts = []

if platform_name == 'Windows':

    extra_scripts.append('bfg9000-setenv=bfg9000.setenv:main')

elif platform_name == 'Linux':

    import hashlib
    import os
    import shutil
    import tarfile
    from setuptools.command.develop import develop as DevelopCommand
    from setuptools.command.install import install as InstallCommand

    try:
        from urllib.request import urlretrieve
    except ImportError:
        from urllib import urlretrieve

    from bfg9000.pathutils import makedirs, pushd

    class InstallPatchelf(Command):
        description = 'install the patchelf executable'
        user_options = [
            ('force', 'f', 'force installation of patchelf, even if already ' +
             'installed'),
            ('prefix=', None, 'prefix to install patchelf to')
        ]

        patchelf_url = ('https://nixos.org/releases/patchelf/patchelf-0.8/' +
                        'patchelf-0.8.tar.gz')
        sha256_hash = ('14af06a2da688d577d64ff8dac065bb8' +
                       '903bbffbe01d30c62df7af9bf4ce72fe')

        def initialize_options(self):
            self.force = False
            self.prefix = os.getenv('VIRTUAL_ENV')

        def finalize_options(self):
            pass

        @staticmethod
        def sha256sum(filename, blocksize=65536):
            sha = hashlib.sha256()
            with open(filename, 'rb') as f:
                for block in iter(lambda: f.read(blocksize), b""):
                    sha.update(block)
            return sha.hexdigest()

        def run(self):
            if not self.force:
                try:
                    output = subprocess.check_output(
                        ['which', 'patchelf'], universal_newlines=True
                    )
                    print('Found patchelf at {}'.format(output.strip()))
                    return
                except:
                    print('patchelf not found, installing...')

            filename = os.path.basename(self.patchelf_url)
            makedirs('build', exist_ok=True)
            with pushd('build'):
                print('Downloading {}...'.format(self.patchelf_url))
                urlretrieve(self.patchelf_url, filename)

                if self.sha256sum(filename) != self.sha256_hash:
                    raise RuntimeError(
                        "{} doesn't match checksum".format(filename)
                    )

                tar = tarfile.open(filename, 'r:gz')
                sub = tar.getnames()[0]

                if os.path.exists(sub):
                    print('Cleaning {}'.format(sub))
                    shutil.rmtree(sub)

                print('Extracting to build/{}'.format(filename))
                tar.extractall('.')

                with pushd(tar.getnames()[0]):
                    configure = ['./configure']
                    if self.prefix:
                        configure += ['--prefix', self.prefix]

                    print('Configuring: {}'.format(' '.join(configure)))
                    subprocess.check_call(configure)

                    print('Building...')
                    subprocess.check_call(['make'])

                    print('Installing...')
                    subprocess.check_call(['make', 'install'])

    no_patchelf = os.getenv('NO_PATCHELF') in ['1', 'true']

    class Develop(DevelopCommand):
        def run(self):
            DevelopCommand.run(self)
            if not no_patchelf:
                self.run_command('install_patchelf')

    class Install(InstallCommand):
        def run(self):
            InstallCommand.run(self)
            if not no_patchelf:
                self.run_command('install_patchelf')

    custom_cmds.update({
        'install_patchelf': InstallPatchelf,
        'develop': Develop,
        'install': Install,
    })

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
    url='http://jimporter.github.io/bfg9000/',

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

    install_requires=['colorama', 'doppel==0.1.0.dev0', 'enum-compat',
                      'packaging', 'six'],
    extras_require={
        'msbuild': ['lxml'],
        'lint': ['flake8'],
        'doc': ['mkdocs', 'mkdocs-bootswatch'],
        'deploy': ['pypandoc'],
    },

    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
            'bfg9000-depfixer=bfg9000.depfixer:main',
        ] + extra_scripts,
        'bfg9000.backends': [
            'make=bfg9000.backends.make.writer',
            'ninja=bfg9000.backends.ninja.writer',
            'msbuild=bfg9000.backends.msbuild.writer [msbuild]',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
