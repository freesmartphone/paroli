#!/bin/sh

# This script will build the edje files for each application
cd paroli-contacts; ./build.sh; cd ..
cd paroli-dialer; ./build.sh; cd ..
cd paroli-i-o; ./build.sh; cd ..
cd paroli-msgs; ./build.sh; cd ..
cd paroli-launcher; ./build.sh; cd ..
cd tele; ./build.sh; cd ..