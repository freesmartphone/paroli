#!/bin/sh -e
echo "building messages.edj..."
edje_cc\
	-id edje/default/images\
	-fd .\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/messages.edc\
	-o messages.edj
