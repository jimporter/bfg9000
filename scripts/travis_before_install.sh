#!/bin/bash

set -ev

echo ${TRAVIS_OS_NAME}
if [ "${TRAVIS_OS_NAME}" = "linux" ]; then
    wget https://nixos.org/releases/patchelf/patchelf-0.8/patchelf-0.8.tar.gz
    tar -xzf patchelf-0.8.tar.gz
    cd patchelf-0.8
    ./configure --prefix=$VIRTUAL_ENV && make && make install
else
    brew update
    brew install python
    brew install libogg
    brew install ninja
fi
