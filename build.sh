#!/usr/bin/env bash


# Setup
DIR=$PWD
MODULES=("pathfind" "camera")

# Compile Cython Modules
for module in "${MODULES[@]}"; do
    cd $DIR/modules/$module
    python3 setup.py build_ext --build-lib=../
done


# Decide whether or not to build main
for arg in "$@"; do
    case $arg in
        -m|--main)
        # Final build
        cd $DIR
        python3 setup.py build
        ;;
    esac
done

