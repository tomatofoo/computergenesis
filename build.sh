#!/usr/bin/env bash

# Setup
DIR=$PWD
MODULES=("pathfind" "camera")

# Compile Cython Modules
for module in $MODULES
do
    cd $DIR/modules/$module
    python3 setup.py build_ext --build-lib=../
done

# Final build
cd $DIR
python3 setup.py build

