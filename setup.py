from setuptools import setup, find_packages
from bfg9000.version import __version__

setup(
    name='bfg9000',
    version=__version__,

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    packages=find_packages(exclude=['test']),
    install_requires=['lxml'],
    entry_points={
        'console_scripts': [
            'bfg9000=bfg9000.driver:main',
            'arachnotron=bfg9000.scanner:scan',
        ],
    },

    test_suite='test',
)
