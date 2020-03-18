/usr/bin/mpg123 --loop -1 /home/pi/testsuite/music.mp3 &

while :
do
	/usr/bin/python3 /home/pi/testsuite/fulltest.py
	sleep 5
done
