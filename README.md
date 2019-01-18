# quick-pi
Tools to enable programming a Raspberry Pi from the QuickAlgo environment

# How to setup

* Download the latest Raspbian Stretch Lite (no GUI needed) version from https://www.raspberrypi.org/downloads/raspbian/, follow the instructions on how to write the image to an SD card here https://www.raspberrypi.org/documentation/installation/installing-images/README.md.

* If you are planing to make this a production ready image reinsert the SD card into the machine you used to write it and go to the drive. You will find a cmdline.txt file. Open it and delete `init=/usr/lib/raspi-config/init_resize.sh
` from the end of the command line. This will prevent the filesystem to be resized to fill the whole size of your sd card.

* Boot the Raspberry Pi (connect a keyboard and display), login with the default pi/raspbian user password.

* Run `sudo raspi-config` and enable SSH (for easier remote management and setup WiFi).

* Install the required dependencies by doing: `sudo apt-get install python3-flask python3-pip python3-rpi.gpio gunicorn3 dos2unix python3-pexpect python3-smbus` then `pip3 install flask-cors Flask-Sockets cffi`.

* Copy the contents of the `server` directory into the Raspberry Pi using scp. This is a flask webapp that will run the programs in the Raspberry Pi. Run it using `python3 quickpi.py`.

* Setup a webserver else where and copy the files in `js` and access index.html. 

* Write the Raspberry Pi IP address in the field and you can start trying programs.

# How to create a production ready image

First run all of the above steps then:

* Add the following command to /etc/rc.local: `su pi -c "cd /home/pi/quickpi; gunicorn3 -k flask_sockets.worker -b 0.0.0.0:5000 quickpi:app"`

* Edit the file /lib/systemd/system/raspberrypi-net-mods.service so it look like this:

```
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/etc/setupwifi.sh
ExecStartPost=/bin/chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf

[Install]
WantedBy=multi-user.target
```

* Delete the wpa_supplicant config file and link it to /tmp like with these commands:

```
rm /etc/wpa_supplicant/wpa_supplicant.conf
ln -s /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf
```

* Move the dhcpcd config and link it to /tmp liek this:

```
mv /etc/dhcpcd.conf /etc/dhcpcd.conf.template
ln -s /tmp/dhcpcd.conf /etc/dhcpcd.conf
```

* Copy the file scripts/setupwifi.sh to /etc and give it execution permisions `chmod +x /etc/setupwifi.sh`

* Download Adafruit script to make the filesystem readonly: `wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/read-only-fs.sh; sudo bash read-only-fs.sh`. Answer N to "Enable boot-time jumper", "Install GPIO-halt utility" and `Enable kernel panic watchdog` so none of those is enabled.

* Create a dummy wifi.txt file in the boot partition with the following contents:

```
SSID=wifiname
PASSWORD=wifipassword
STATICNETWORK=1
STATICIPADDR=192.168.1.31
```

* Shutdown the Raspberry Pi using `sudo halt`. Remove the raspberry pi and take an image of the SD card of the exact same size of the original Raspbian Image you started with.

