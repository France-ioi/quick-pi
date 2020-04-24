#!/bin/bash

VERSION=$(cat /home/pi/quickpi/version)
BASEURL="https://mapadev.com/test/quickpi/"

echo "Current version: $VERSION"
echo "Checking for new version..."

curl $BASEURL"version" --output /tmp/version

NEWVERSION=$(cat /tmp/version)

if [ "$VERSION" == "$NEWVERSION" ]
then
	echo "Already at latest version $NEWVERSION"
	exit 0
fi

echo "New version $NEWVERSION found"
echo "Downloading ..."
curl "$BASEURL""quickpi.tar.gz" --output /tmp/quickpi.tar.gz
RESULT=$?

if [ $RESULT != "0" ]; then
	echo "Error when downloading update"
	exit 1
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

echo "Post update unkeeping..."
cp -f /tmp/version /home/pi/quickpi/
sudo /home/pi/quickpi/scripts/afterupdate.sh

echo "Sucess, restarting ..."

sleep 3
sudo reboot
