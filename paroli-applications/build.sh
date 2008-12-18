#!/bin/sh

# I do this very quickly and it is ugly
cd paroli-contacts; ./build.sh; cd ..
cd paroli-dialer; ./build.sh; cd ..
cd paroli-i-o; ./build.sh; cd ..
cd paroli-msgs; ./build.sh; cd ..