var is_ssid_combo = false;

function openTab(evt, cityName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(cityName).style.display = "block";
  evt.currentTarget.className += " active";
} 

function save()
{
	var isstaticip = document.getElementById('staticip').checked;
	var ip = document.getElementById('ip').value;
	var sn = document.getElementById('sn').value;
	var gw = document.getElementById('gw').value;
	var ns = document.getElementById('ns').value;
	var isbluetoothenabled = document.getElementById('bluetooth').checked;

	var school = document.getElementById('school').value;
	var qname = document.getElementById('qname').value;

	var ssid = "";
	if (is_ssid_combo)
	{
		var ssidselect = document.getElementById('ssid_select');
		ssid = ssidselect.options[ ssidselect.selectedIndex ].value;
	} else {
		ssid = document.getElementById('ssid_input').value;     
	}
	var password = document.getElementById('password').value;

	var data = {
		ip: ip,
		sn: sn,
		ns: ns,
		gw: gw,
		isstaticip: isstaticip,
		ssid: ssid,
		password: password,
		isbluetoothenabled : isbluetoothenabled,
		school: school,
		qname: qname
	};

	fetch('savesettings', {
		method: 'POST',	
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(data)
	})
	.then((response) => {
		alert("Settings saved");
	})
	.catch((error) => {
		alert("Error saving settings");
	})
}

function get_wifinetworks()
{
	fetch('wifinetworks.json')
		.then((response) => {
                return response.json();
            })
            .then((myJson) => {
                var ssidselect = document.getElementById('ssid_select');
                document.getElementById("ssid_input").style.display = "none";
                document.getElementById("ssid_select").style.display = "block";
                is_ssid_combo = true;

                for(var i = ssidselect.options.length - 1 ; i >= 0 ; i--)
                {
                    ssidselect.remove(i);
                }

                for(var i = 0; i < myJson.length; i++)
                {
                    var option = document.createElement("option");
                    option.text = myJson[i];
                    option.value = myJson[i];
                    ssidselect.add(option);
                }
            });
}



function get_log(logfile)
{
	fetch("/log/" + logfile)
		.then((response) => {
			return response.text();
		})
		.then((data) => {

			textarea = document.getElementById(logfile + "_area");

			textarea.value = data;
		});

}

function getlog_syslog()
{
	get_log("syslog");
}

function getlog_dmesg()
{
	get_log("dmesg");
}

function getlog_journalctl()
{
	get_log("journalctl");
}

function initialize()
{
        fetch('/getsettings.json')
                .then((response) => {
                return response.json();
            })
            .then((myJson) => {

		document.getElementById('ssid_input').value = myJson.SSID;
		document.getElementById("ssid_select").style.display = "none";

	        document.getElementById('staticip').checked = myJson.STATICNETWORK == "1" ? true : false;
	        document.getElementById('ip').value = myJson.STATICIPADDR;

	        document.getElementById('sn').value = myJson.STATICSUBNET;

	        document.getElementById('gw').value = myJson.STATICGATEWAY;
	        document.getElementById('ns').value = myJson.STATICDNS;
	        document.getElementById('bluetooth').checked = myJson.ENABLEBLUETOOTH == "1" ? true : false;

        	document.getElementById('school').value = myJson.SCHOOL;
	        document.getElementById('qname').value = myJson.NAME;

            });

	openTab(event, 'config');
}
