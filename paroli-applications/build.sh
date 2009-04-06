#!/bin/sh

# This script will build the edje files for each application
cd i-o2; ./build.sh; cd ..
cd paroli-launcher2; ./build.sh; cd ..
cd tele2; ./build.sh; cd ..
cd msgs2; ./build.sh; cd ..
cd people2; ./build.sh; cd ..
cd settings; ./build.sh; cd ..

