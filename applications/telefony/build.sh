#!/bin/sh -e
echo "building tele.edj..."
edje_cc\
	-id edje/default/images\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/tele.edc\
	-o tele.edj
