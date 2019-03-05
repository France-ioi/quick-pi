source /tmp/wifi.txt

while [ 1 ]
do
	MYIP=$(hostname -I | awk '{$1=$1};1')

	curl --header "Content-Type: application/json" \
	  --request POST \
	  --data "{\"ip\": \"$MYIP\", \"name\":\"$NAME\",  \"school\":\"$SCHOOL\"}" \
	  http://france-ioi.org/QuickPi/ping.php

	sleep 30
done
