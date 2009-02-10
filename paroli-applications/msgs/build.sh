#!/bin/sh
edje_cc $@ -id edje/default/images -fd . edje/default/msgs.edc -o msgs.edj
chmod +r msgs.edj
