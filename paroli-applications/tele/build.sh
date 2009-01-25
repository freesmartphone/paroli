#!/bin/sh
edje_cc $@ -id edje/default/images -fd . edje/default/tele.edc -o tele.edj
chmod +r tele.edj
