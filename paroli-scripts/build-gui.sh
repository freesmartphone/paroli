#! /bin/sh

echo "cd ../paroli-applications"
cd ../paroli-applications
echo "./build.sh $@"
./build.sh $@
echo "cd ../paroli-scripts"
cd ../paroli-scripts

