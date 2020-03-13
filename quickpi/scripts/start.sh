#!/bin/bash

service ntp stop
/usr/lib/ntp/ntp-systemd-wrapper

DISABLETUNNEL="0"
source /tmp/quickpi.txt

cd /home/pi/quickpi
su pi -c "cd /home/pi/quickpi; gunicorn3 -k flask_sockets.worker -b 0.0.0.0:5000 quickpi:app" &
su pi -c "/home/pi/quickpi/install.sh run" &

su - pi -c "/home/pi/quickpi/scripts/ping.sh &"

/home/pi/quickpi/scripts/startbluetooth.sh &


#pigpiod -x -1

pigs m 19 5
pigs m 18 5

iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000

iptables -t nat -A PREROUTING -i ap0 -p tcp --dport 80 -j REDIRECT --to-port 5000
iptables -t nat -A PREROUTING -i ap0 -p tcp --dport 443 -j REDIRECT --to-port 5000

/usr/bin/python3 /home/pi/quickpi/scripts/quickpimenu.py &

TUNNELCODE="$SCHOOL-$NAME"

if [ $TUNNELCODE != "schoolkey-quickpi1" ] && [ $DISABLETUNNEL == "0" ]; then
	/usr/bin/python3 /home/pi/quickpi/scripts/qt-client.py "$TUNNELCODE" &
fi

exit 0

