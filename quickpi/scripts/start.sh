#!/bin/bash

service ntp stop
/usr/lib/ntp/ntp-systemd-wrapper

DISABLETUNNEL="0"
source /tmp/quickpi.txt

/home/pi/quickpi/scripts/runserver.sh

if [ -f "/mnt/data/installedprogram.py" ]; then

	set +e
	/usr/bin/python3 /home/pi/quickpi/scripts/quickpimenu.py  --asktocancel 8

	if [ "$?" == "0" ]; then
		su pi -c "/home/pi/quickpi/install.sh run" &
	else
		/usr/bin/python3 /home/pi/quickpi/scripts/quickpimenu.py &
	fi
else
	/usr/bin/python3 /home/pi/quickpi/scripts/quickpimenu.py &
fi


/usr/bin/python3 /home/pi/quickpi/scripts/restart.py &

su - pi -c "/home/pi/quickpi/scripts/ping.sh &"

/home/pi/quickpi/scripts/startbluetooth.sh &


#pigpiod -x -1

pigs m 19 5
pigs m 18 5

iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000

iptables -t nat -A PREROUTING -i ap0 -p tcp --dport 80 -j REDIRECT --to-port 5000
iptables -t nat -A PREROUTING -i ap0 -p tcp --dport 443 -j REDIRECT --to-port 5000

TUNNELCODE="$SCHOOL-$NAME"

if [ $TUNNELCODE != "schoolkey-quickpi1" ] && [ $DISABLETUNNEL == "0" ]; then

	su - pi -c "/usr/bin/python3 /home/pi/quickpi/scripts/qt-client.py $TUNNELCODE &"
fi

exit 0

