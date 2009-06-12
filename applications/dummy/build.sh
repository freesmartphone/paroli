#!/bin/sh -e
echo "building dummy.edj..."
edje_cc\
	-id ../../resources/images\
	-fd ../../resources/fonts\
	dummy.edc\
	-o dummy.edj
