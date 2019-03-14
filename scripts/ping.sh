#!/bin/bash

source /tmp/quickpi.txt

if [ $DISABLEPING -eq "1" ]; then
    exit;
fi

TIME_BOOT_ORIG=$(/bin/date +%s)
echo $TIME_BOOT_ORIG

while [ 1 ]
do
	MYIP=$(ip addr show wlan0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1 | /usr/bin/awk '{$1=$1};1')

	TIME_CONNECTION=$(/bin/cat /tmp/time-connection)
	TIME_INSTALL=$(/bin/cat /tmp/time-install)
	TIME_SESSION=$(/bin/cat /tmp/time-session)
	TIME_CURRENT=$(/bin/date +%s)

	if [ -z "$TIME_CONNECTION" ]; then
		TIME_CONNECTION=-1
	else
		TIME_CONNECTION=$(expr $TIME_CURRENT - $TIME_CONNECTION)
	fi

        if [ -z "$TIME_INSTALL" ]; then
                TIME_INSTALL=-1
	else
		TIME_INSTALL=$(expr $TIME_CURRENT - $TIME_INSTALL)
        fi

        if [ -z "$TIME_SESSION" ]; then
                TIME_SESSION=-1
	else
		TIME_SESSION=$(expr $TIME_CURRENT - $TIME_SESSION)
        fi

	/usr/bin/curl --request POST \
	 -F "ip=$MYIP" -F "name=$NAME" -F "school=$SCHOOL" \
	 -F "last_connection=$TIME_CONNECTION" -F "last_install=$TIME_INSTALL" -F "last_session=$TIME_SESSION" -F "last_boot=$TIME_BOOT" \
	  http://www.france-ioi.org/QuickPi/ping.php

	echo "done"


	sleep 30
done
