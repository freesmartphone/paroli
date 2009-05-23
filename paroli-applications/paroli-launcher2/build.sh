#!/bin/sh

echo "building paroli-launcher.edj..."
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/paroli-launcher.edc -o paroli-launcher.edj
chmod +r paroli-launcher.edj
