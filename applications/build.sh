#!/bin/sh -e
for d in *; do
	if [ -x $d/build.sh ] ; then
		export d
		(cd $d && ./build.sh)
	fi
done
