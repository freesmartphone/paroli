#!/bin/sh -e
echo "building launcher.edj..."
edje_cc\
	-id edje/default/images\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/launcher.edc\
	-o launcher.edj
