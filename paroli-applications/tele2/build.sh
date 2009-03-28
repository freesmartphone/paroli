#!/bin/sh
edje_cc $@ -id edje/default/images -id ../common-for-edje/images -fd ../common-for-edje/fonts edje/default/tele.edc -o tele.edj
chmod +r tele.edj
