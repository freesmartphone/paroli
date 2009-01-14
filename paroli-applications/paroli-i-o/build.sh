#!/bin/sh
edje_cc $@ -id edje/default/images -fd . edje/default/paroli-i-o.edc -o paroli-i-o.edj
chmod +r paroli-i-o.edj
