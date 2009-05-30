#!/bin/sh -e

flag_io=
flag_launcher=
flag_msgs=
flag_people=
flag_settings=
flag_tele=

while getopts 'ilmpst' OPTION
do
  case $OPTION in
  i)	flag_io=1
	;;
  l)	flag_launcher=1
	;;
  m)	flag_msgs=1
	;;
  p)	flag_people=1
	;;
  s)	flag_settings=1
	;;
  t)	flag_tele=1
	;;
  ?)	printf "Usage: %s: [-i] [-l] [-m] [-p] [-s] [-t]\n" $(basename $0) >&2
	exit 2
	;;
  esac
done

if [[ "$flag_io" -eq "0" && "$flag_launcher" -eq "0" && \
       "$flag_msgs" -eq "0" && "$flag_people" -eq "0" && \
       "$flag_settings" -eq "0" && "$flag_tele" -eq "0" ]]
then
	flag_io=1
	flag_launcher=1
	flag_msgs=1
	flag_people=1
	flag_settings=1
	flag_tele=1
fi

# This script will build the edje files for each application
if [ "$flag_io" ]
then
	cd inout; ./build.sh; cd ..
fi
if [ "$flag_launcher" ]
then
	cd launcher; ./build.sh; cd ..
fi
if [ "$flag_msgs" ]
then
	cd letters; ./build.sh; cd ..
fi
if [ "$flag_people" ]
then
	cd people; ./build.sh; cd ..
fi
if [ "$flag_settings" ]
then
	cd settings; ./build.sh; cd ..
fi
if [ "$flag_tele" ]
then
	cd telefony; ./build.sh; cd ..
fi

