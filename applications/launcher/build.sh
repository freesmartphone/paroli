#!/bin/sh -e
echo "building paroli-launcher.edj..."
edje_cc\
	-id edje/default/images\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/paroli-launcher.edc\
	-o paroli-launcher.edj
