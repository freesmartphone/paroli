#!/bin/sh -e
echo "building telephony.edj..."
edje_cc\
	-id edje/default/images\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/telephony.edc\
	-o telephony.edj
