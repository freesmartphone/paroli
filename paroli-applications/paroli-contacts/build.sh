#!/bin/sh
edje_cc $@ -id edje/default/images -fd ../common-for-edje/fonts edje/default/paroli-contacts.edc -o paroli-contacts.edj
chmod +r paroli-contacts.edj
