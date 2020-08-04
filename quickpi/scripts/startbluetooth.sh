#!/bin/bash

ENABLEBLUETOOTH=0
OLDIFS=$IFS
IFS="="
while read -r name value; do
        if [ -n "$name" ] && [[ "$name" != "#"* ]]; then
                echo "Content of $name is ${value//\"/}"
                export "$name"="$value"
        fi
done < /tmp/quickpi.txt
IFS=$OLDIFS

if [ $ENABLEBLUETOOTH -ne "1" ]; then
    exit;
fi


/sbin/brctl addbr pan0

/usr/bin/bt-network -s nap pan0 &
sleep 1
/usr/bin/bt-agent -c NoInputNoOutput &

/usr/bin/bt-adapter --set Alias $NAME
/usr/bin/bt-adapter --set DiscoverableTimeout 0
/usr/bin/bt-adapter --set Discoverable 1


