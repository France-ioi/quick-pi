su pi -c "cd /home/pi/quickpi; gunicorn3 -k flask_sockets.worker -b 0.0.0.0:5000 quickpi:app" &
su pi -c "/home/pi/quickpi/install.sh run" &
/home/pi/quickpi/scripts/ping.sh &
/home/pi/quickpi/scripts/startbluetooth.sh &


#pigpiod -x -1

pigs m 19 5
pigs m 18 5

iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000

exit 0

