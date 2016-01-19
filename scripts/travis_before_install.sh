#!/bin/bash

set -ev

if [ "${TRAVIS_OS_NAME}" = "osx" ]; then
    brew update
    brew install python
    brew install coreutils
    brew install ninja
    brew install libogg
fi
