#! /bin/sh -e
echo "cd ../applications"
cd ../applications
echo "./build.sh $@"
./build.sh $@
echo "cd ../scripts"
cd ../scripts
