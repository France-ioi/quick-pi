#!/bin/bash

cp /boot/wifi.txt /tmp
dos2unix /tmp/wifi.txt
source /tmp/wifi.txt

echo "
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=MX

network={
        ssid=\"$SSID\"
        psk=\"$PASSWORD\"
}
" > /tmp/wpa_supplicant.conf

cp /etc/dhcpcd.conf.template /tmp/dhcpcd.conf
if [ $STATICNETWORK -eq "1" ]; then
	echo "Static network config"
	echo "
interface wlan0
static ip_address=$STATICIPADDR" >> /tmp/dhcpcd.conf
fi
