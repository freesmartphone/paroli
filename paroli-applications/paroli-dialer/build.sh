#!/bin/sh
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/paroli-dialer.edc -o paroli-dialer.edj
chmod +r paroli-dialer.edj
