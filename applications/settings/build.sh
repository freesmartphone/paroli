#!/bin/sh -e
echo "building settings.edj"
edje_cc\
	-id .\
	-fd .\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/settings.edc\
	-o settings.edj
