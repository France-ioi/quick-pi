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

