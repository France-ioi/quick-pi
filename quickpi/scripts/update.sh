#!/bin/bash

VERSION=$(cat /home/pi/quickpi/version)
BASEURL="http://quick-pi.org/update/"

NEWVERSION=$1
HAVEFILE=""
if [ $NEWVERSION != "" ]; then
	HAVEFILE="yes"
fi


echo "Current version: $VERSION"
echo "Update version: $NEWVERSION"

if [ "$NEWVERSION" != "" ]; then
	curl $BASEURL"version" --output /tmp/version

	NEWVERSION=$(cat /tmp/version)
fi

if [ "$VERSION" -ge "$NEWVERSION" ]
then
	echo "Server version $NEWVERSION not updating"
	exit 0
fi

if [ "$HAVEFILE" != "" ]; then
	echo "New version $NEWVERSION found"
	echo "Downloading ..."
	curl "$BASEURL""quickpi.tar.gz" --output /tmp/quickpi.tar.gz
	RESULT=$?

	if [ $RESULT != "0" ]; then
		echo "Error when downloading update"
		exit 1
	fi
fi

echo "Uncompressing update..."
sudo mount / -o remount,rw
RESULT=$?
if [ $RESULT != "0" ]; then
        echo "Failed to remount system as r/w"
	exit 1
fi

tar xvfzp /tmp/quickpi.tar.gz -C /home/pi/
RESULT=$?
if [ $RESULT != "0" ]; then
        echo "Error when uncompressing update"
        exit 1
fi

echo "Post update upkeeping..."
echo $NEWVERSION > /home/pi/quickpi/version
sudo /home/pi/quickpi/scripts/afterupdate.sh

echo "Sucess, restarting ..."

sleep 8
sudo reboot
