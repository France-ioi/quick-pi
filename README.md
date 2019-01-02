# quick-pi
Tools to enable programming a Raspberry Pi from the QuickAlgo environment

# How to setup

* Download the latest Raspbian Stretch Lite (no GUI needed) version from https://www.raspberrypi.org/downloads/raspbian/, follow the instructions on how to write the image to an SD card here https://www.raspberrypi.org/documentation/installation/installing-images/README.md.

* Boot the Raspberry Pi (connect a keyboard and display), login with the default pi/raspbian user password.

* Run `sudo raspi-config` and enable SSH (for easier remote management and setup WiFi).

* Install the required dependencies by doing: `sudo apt-get install python3-flask python3-pip python3-rpi.gpio` then `pip3 install flask-cors`.

* Copy the contents of the `server` directory into the Raspberry Pi using scp. This is a flask webapp that will run the programs in the Raspberry Pi. Run it using `python3 quickpi.py`.

* Setup a webserver else where and copy the files in `js` and access index.html. 

* Write the Raspberry Pi IP address in the field and you can start trying programs.