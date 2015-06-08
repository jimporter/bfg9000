from setuptools import setup, find_packages
from bfg9000.version import __version__

setup(
    name='bfg9000',
    version=__version__,
    license='BSD',

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',

    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': ['bfg9000=bfg9000.driver:main'],
    },

    test_suite='test',
)
