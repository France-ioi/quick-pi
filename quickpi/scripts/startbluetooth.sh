#!/bin/bash

OLDIFS=$IFS
IFS="="
while read -r name value; do
        if [ -n "$name" ] && [[ "$name" != "#"* ]]; then
                #echo "Content of $name is ${value//\"/}"
                export "$name"="$value"
        fi
done < /tmp/quickpi.txt
IFS=$OLDIFS

if [ "$1" == "start" ]; then
	/sbin/brctl addbr pan0

	/usr/bin/bt-network -s nap pan0 &
	sleep 1
	/usr/bin/bt-agent -c NoInputNoOutput &

	/usr/bin/bt-adapter --set Alias $NAME
	/usr/bin/bt-adapter --set DiscoverableTimeout 0
	/usr/bin/bt-adapter --set Discoverable 1
else
	pkill -9 bt-network
	pkill -9 bt-agent

	/sbin/ifconfig pan0 down
	/sbin/brctl delbr pan0
fi

