# quick-pi
Tools to enable programming a Raspberry Pi from the QuickAlgo environment


# How to setup

* Download the latest Raspbian Buster Lite (no GUI needed) version from https://www.raspberrypi.org/downloads/raspbian/, follow the instructions on how to write the image to an SD card here https://www.raspberrypi.org/documentation/installation/installing-images/README.md.

* If you are planing to make this a production ready image reinsert the SD card into the machine you used to write it and go to the drive. You will find a cmdline.txt file. Open it and delete `init=/usr/lib/raspi-config/init_resize.sh
` from the end of the command line. This will prevent the filesystem to be resized to fill the whole size of your sd card.

* Boot the Raspberry Pi (connect a keyboard and display), login with the default pi/raspbian user password.

* Create a 100M partition after the root partition to store the installed program (the root partition is read only):

```
echo -e "n\n\n\n4292608\n+100M\nw\nq\n" | fdisk /dev/mmcblk0
partprobe

mkfs.ext4 /dev/mmcblk0p3
mkdir /mnt/data
chown pi.pi /mnt/data/
echo "/dev/mmcblk0p3 /mnt/data ext4 defaults 0 2" >> /etc/fstab
```


* Run `sudo raspi-config` and enable SSH (for easier remote management and setup WiFi), also enable I2C (Needed for analog sensors).

* Install the required dependencies by doing: `sudo apt-get install python3-flask python3-pip python3-rpi.gpio gunicorn3 dos2unix python3-pexpect python3-smbus pigpio python3-pigpio  bluez-tools dnsmasq bridge-utils python3-pil hostapd` then `sudo pip3 install flask-cors Flask-Sockets luma.oled adafruit-circuitpython-vl53l0x`. `sudo systemctl enable pigpiod`

* Copy the contents of the `server` directory into /home/pi/quickpi/ in the Raspberry Pi using scp. This is a flask webapp that will run the programs in the Raspberry Pi.


# How to create a production ready image

First run all of the above steps then:

* Add `dtoverlay=dwc2,dr_mode=peripheral` to the bottom of /boot/config.txt

* Add `modules-load=dwc2,g_ether` in /boot/cmdline.txt right next to `rootwait`. Don't introduce new lines into this file.

* Edit /lib/systemd/system/pigpiod.service to change pigpiod command line to the following `/usr/bin/pigpiod -n 127.0.0.1 -l -m -x -1`

* Add the following command to /etc/rc.local:

```
/home/pi/quickpi/scripts/start.sh &
```

* Edit the file /lib/systemd/system/raspberrypi-net-mods.service so it look like this:

```
[Unit]
Description=Copy user wpa_supplicant.conf
Before=dhcpcd.service
After=systemd-rfkill.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/etc/setupwifi.sh
ExecStartPost=/bin/chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf
ExecStartPost=/usr/sbin/rfkill unblock wifi

[Install]
WantedBy=multi-user.target
```

* Delete the wpa_supplicant config file and link it to /tmp like with these commands:

```
rm /etc/wpa_supplicant/wpa_supplicant.conf
ln -s /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
```

* Move the dhcpcd config and link it to /tmp:

```
mv /etc/dhcpcd.conf /etc/dhcpcd.conf.template
ln -s /tmp/dhcpcd.conf /etc/dhcpcd.conf
```

Same with hostapd config file:

```
rm -f /etc/hostapd/hostapd.conf 
ln -s /etc/hostapd/hostapd.conf /tmp/hostapd.conf
```

* Add the following to the bottom of /etc/dhcpcd.conf.template

```
interface usb0
static ip_address=192.168.233.1

denyinterfaces ap0
interface ap0
nohook wpa_supplicant

```

* Edit /etc/dnsmasq.conf so that this is the entiere contents:

```
interface=usb0
interface=ap0
dhcp-range=192.168.233.10,192.168.233.230,2h
dhcp-option=usb0,3
dhcp-option=usb0,6
address=/#/192.168.233.3
```

* Edit /etc/default/dnsmasq to add at the bottom:

```
DNSMASQ_EXCEPT=lo
```



* Delete /var/lib/ and link it to /tmp
```
rm -rf /var/lib/misc
ln -s /tmp /var/lib/misc 
```

* Create a dummy quickpi.txt file in /boot with the following contents:

```
SSID=wifiname
PASSWORD=wifipassword
STATICNETWORK=1
STATICIPADDR=192.168.1.31
STATICGATEWAY=192.168.1.1
STATICDNS=8.8.8.8

NAME=quickpi1
SCHOOL=schoolkey
SCHOOLPASSWORD=schoolpassword
```

* Download Adafruit script to make the filesystem readonly: `wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/read-only-fs.sh; sudo bash read-only-fs.sh`. Answer N to "Enable boot-time jumper", "Install GPIO-halt utility" and `Enable kernel panic watchdog` so none of those is enabled.

* Shutdown the Raspberry Pi using `sudo halt`. Remove the raspberry pi and take an image of the SD card of the same size plus 100M (add a bit to be sure) of the original Raspbian Image you started with.

