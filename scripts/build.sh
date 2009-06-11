#! /bin/sh -e
echo "./build.sh $@"
cd ../applications && ./build.sh $@
