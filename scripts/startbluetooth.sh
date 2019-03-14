#!/bin/bash

source /tmp/quickpi.txt

if [ $ENABLEBLUETOOTH -ne "1" ]; then
    exit;
fi


source /tmp/wifi.txt

/sbin/brctl addbr pan0

/usr/bin/bt-network -s nap pan0 &
sleep 1
/usr/bin/bt-agent -c NoInputNoOutput &

/usr/bin/bt-adapter --set Alias $NAME
/usr/bin/bt-adapter --set DiscoverableTimeout 0
/usr/bin/bt-adapter --set Discoverable 1


