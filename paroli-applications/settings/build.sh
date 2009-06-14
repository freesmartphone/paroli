#!/bin/sh

echo "building settings.edj"
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd . -fd ../common-for-edje/fonts edje/default/settings.edc -o settings.edj
chmod +r settings.edj
