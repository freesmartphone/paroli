#!/bin/sh -e

echo "building settings.edj"
edje_cc $@ -id . -id ../../resources/images -fd . -fd ../../resources/fonts edje/default/settings.edc -o settings.edj
chmod +r settings.edj
