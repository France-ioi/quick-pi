source /tmp/wifi.txt

while [ 1 ]
do
	MYIP=$(hostname -I | awk '{$1=$1};1')
	NAME=pi1
	SCHOOL=school1

	echo $MYIP

	curl --header "Content-Type: application/json" \
	  --request POST \
	  --data "{\"ip\": \"$MYIP\", \"name\":\"$NAME\",  \"school\":\"$SCHOOL\"}" \
	  http://france-ioi.org/QuickPi/ping.php

	sleep 30
done