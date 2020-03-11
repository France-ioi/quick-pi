if [ "$1" = "station" ]; then
	sudo systemctl stop hostapd
#	sudo systemctl stop dhcpcd
	#sudo /sbin/dhcpcd -x
	sudo ip link set ap0 down
	sudo systemctl stop dhcpcd
	sudo ip link set ap0 name wlan0
	#sudo ip addr del 192.168.233.2/24 dev wlan0
	sudo ifconfig wlan0 0.0.0.0
	sudo ip link set wlan0 up
        sudo wpa_cli enable_network 0

	sudo systemctl start dhcpcd
else
	sudo wpa_cli disable_network 0
	sudo systemctl stop dhcpcd
	sudo ip link set wlan0 down
	sudo ip link set wlan0 name ap0
	#sudo ip addr add 192.168.233.2/24 dev ap0
	sudo ifconfig ap0 192.168.233.3
	sudo ip link set ap0 up
	sudo systemctl start hostapd
	sudo systemctl start dhcpcd
fi
