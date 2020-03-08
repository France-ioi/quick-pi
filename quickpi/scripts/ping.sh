#!/bin/bash

FIRSTTIME=1
DISABLEPING=0


/home/pi/quickpi/script/showtext.py "Initialized"
if [ ! -f /tmp/quickpi.txt ]; then
	/home/pi/quickpi/script/showtext.py "quickpi.txt" "DOES NOT EXISTS"

	exit 0
fi

source /tmp/quickpi.txt
status=$?
set +e
if [  "$status" -ne "0" ]; then
	/home/pi/quickpi/script/showtext.py "quickpi.txt" "WRONG FORMAT"
	sleep 5
fi

if [ -z "$SSID" ] || [ -z "$PASSWORD" ]  || [ -z "$STATICNETWORK" ]; then
	/home/pi/quickpi/script/showtext.py "quickpi.txt" "MISING FIELDS"
fi


if [ "$DISABLEPING" -eq "1" ]; then
    exit;
fi

MYMAC=$(ip addr show wlan0 | grep "ether\b" | awk '{print $2}' | cut -d/ -f1 | /usr/bin/awk '{$1=$1};1')
MYACPART1=$(echo $MYMAC | cut -d ":" -f 1)
MYACPART2=$(echo $MYMAC | cut -d ":" -f 2-)


TIME_BOOT_ORIG=$(/bin/date +%s)
echo $TIME_BOOT_ORIG

while [ 1 ]
do
	MYIP=$(ip addr show wlan0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1 | /usr/bin/awk '{$1=$1};1')

	if [ -f "/tmp/time-connection" ]; then
		TIME_CONNECTION=$(/bin/cat /tmp/time-connection)
	fi

	if [ -f "/tmp/time-install" ]; then
		TIME_INSTALL=$(/bin/cat /tmp/time-install)
	fi

	if [ -f "/tmp/time-session" ]; then
		TIME_SESSION=$(/bin/cat /tmp/time-session)
	fi

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
	-F "school_password=$SCHOOLPASSWORD" \
	  http://www.france-ioi.org/QuickPi/ping.php

	echo $(hostname -I)
	echo $(ifconfig)
	echo $(iwconfig)
	echo "-----------------------------------------"

	status=$?


	## Show status only when there hasn't been any connections
	if [ ! -f "/tmp/time-connection" ]; then
		if [ "$status" -eq "0" ]; then
			echo "done"
		elif [ "$status" -eq "6" ]; then
			/home/pi/quickpi/script/showtext.py "Failed to ping" "DNS ERROR"
		elif [ "$status" -eq "7" ]; then
			/home/pi/quickpi/script/showtext.py "Failed to ping" "CANT CONNECT"
		else
			echo "what"
			/home/pi/quickpi/script/showtext.py "Failed to ping" "SERVER ERROR"
		fi

		sleep 10

		WIFISTATUS=$(cat /sys/class/net/wlan0/carrier)
		if [  "$WIFISTATUS" -ne "1" ]; then
		        /home/pi/quickpi/script/showtext.py "WIFI" "CANT CONNECT"
		else
			/home/pi/quickpi/script/showtext.py "WIFI IP" "$MYIP"
		fi

		sleep 10

		/home/pi/quickpi/script/showtext.py "WIFI MAC $MYACPART1:" "$MYACPART2"
	fi

	sleep 30
done
