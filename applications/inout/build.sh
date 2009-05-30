#!/bin/sh -e
echo "building i-o.edj..."
edje_cc\
	-id edje/default/images\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	edje/default/i-o.edc\
	-o i-o.edj
