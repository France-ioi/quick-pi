#!/bin/bash

pkill -9 -f installedprogram.py
pkill -9 gunicorn3
rm /tmp/time-connection
rm /tmp/lock
cd /home/pi/quickpi
su pi -c "cd /home/pi/quickpi; gunicorn3 -k flask_sockets.worker -b 0.0.0.0:5000 -t 60 quickpi:app" &

