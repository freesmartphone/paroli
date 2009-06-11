#!/bin/sh -e
echo "building msgs.edj..."
edje_cc\
	-id edje/default/images\
	-fd .\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/msgs.edc\
	-o msgs.edj
