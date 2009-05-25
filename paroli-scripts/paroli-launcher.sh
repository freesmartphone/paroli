#!/bin/sh
cd /usr/share/nfs-paroli/paroli-scripts/

DISPLAY=:0 \
PYTHONPATH=../paroli-services \
python paroli --cfgfile ./paroli.cfg
