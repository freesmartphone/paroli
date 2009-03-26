#!/bin/sh
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/i-o.edc -o i-o.edj
chmod +r i-o.edj
