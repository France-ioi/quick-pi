#!/bin/bash

INSTALLFILE=/mnt/data/installedprogram.py

if [ $1 == "install" ]; then
	cp $2 $INSTALLFILE
fi

if [ $1 == "run" ]; then
	if [ -f $INSTALLFILE ]; then
		echo "Starting installed file"
		nice -n 19 python3 $INSTALLFILE &
	fi
fi

if [ $1 == "clean" ]; then
	pkill -9 -f $(basename $INSTALLFILE)
	rm -f $2 $INSTALLFILE
fi

