#!/bin/sh
cd /usr/share/paroli/scripts/

DISPLAY=:0 \
python paroli --cfgfile ./paroli.cfg
