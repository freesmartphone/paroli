#!/bin/sh

echo "building calculator.edj..."
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/calculator.edc -o calculator.edj
chmod +r calculator.edj

