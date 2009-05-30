#!/bin/sh -e

echo "building msgs.edj..."
edje_cc $@ -id edje/default/images -id ../../resources/images -fd . edje/default/msgs.edc -fd ../../resources/fonts -o msgs.edj
chmod +r msgs.edj

