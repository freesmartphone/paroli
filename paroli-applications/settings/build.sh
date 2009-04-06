#!/bin/sh
edje_cc $@ -id . -id ../common-for-edje/images -fd . -fd ../common-for-edje/fonts edje/default/settings.edc -o settings.edj
