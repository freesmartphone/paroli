#!/bin/sh
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/paroli-i-o.edc -o paroli-i-o.edj
chmod +r paroli-i-o.edj
