#!/bin/sh

echo "building msgs.edj..."
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd . edje/default/msgs.edc -fd ../common-for-edje/fonts -o msgs.edj
chmod +r msgs.edj

