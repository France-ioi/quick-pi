#!/bin/bash

cp /boot/quickpi.txt /tmp/quickpi-tmp.txt
dos2unix /tmp/quickpi-tmp.txt
echo "set -e" > /tmp/quickpi.txt
cat /tmp/quickpi-tmp.txt >> /tmp/quickpi.txt

OLDIFS=$IFS
IFS="="
while read -r name value; do
        if [ -n "$name" ] && [[ "$name" != "#"* ]]; then
                echo "Content of $name is ${value//\"/}"
                export "$name"="$value"
        fi
done < /tmp/quickpi.txt
IFS=$OLDIFS


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
static ip_address=$STATICIPADDR
static routers=$STATICGATEWAY
static domain_name_servers=$STATICDNS" >> /tmp/dhcpcd.conf
fi

/sbin/dhcpcd -n


if [ $USEPROXY -eq "1" ]; then

	if [ $USEPROXYUSER -eq "1" ]; then
		echo "http_proxy=http://$PROXYUSER:$PROXYPASSWORD@$PROXYADDRESS:$PROXYPORT/
https_proxy=https://$PROXYUSER:$PROXYPASSWORD@$PROXYADDRESS:$PROXYPORT/
export http_proxy
export https_proxy
" > /tmp/proxy.sh 
	else
echo "http_proxy=http://$PROXYADDRESS:$PROXYPORT/
https_proxy=https://$PROXYADDRESS:$PROXYPORT/
export http_proxy
export https_proxy
" > /tmp/proxy.sh

	fi
fi

