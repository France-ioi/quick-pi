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

function staticIpClicked()
{
	var isstaticip = document.getElementById('staticip').checked;

        var ip = document.getElementById('ip');
        var sn = document.getElementById('sn');
        var gw = document.getElementById('gw');
        var ns = document.getElementById('ns');

	ip.disabled = !isstaticip;
	sn.disabled = !isstaticip;
	gw.disabled = !isstaticip;
	ns.disabled = !isstaticip;
}

function proxyAuthClicked()
{
	var useproxyuser = document.getElementById('useproxyuser').checked;
        var proxyuser = document.getElementById('proxyuser');
        var proxypassword = document.getElementById('proxypassword');

        proxyuser.disabled = !useproxyuser;
        proxypassword.disabled = !useproxyuser;
}

function proxyClicked()
{
        var useproxy = document.getElementById('useproxy').checked;

        var proxyaddress = document.getElementById('proxyaddress');
        var proxyport = document.getElementById('proxyport');

        var proxyuser = document.getElementById('proxyuser');
        var proxypassword = document.getElementById('proxypassword');
        var useproxyuser = document.getElementById('useproxyuser');

        proxyaddress.disabled = !useproxy;
        proxyport.disabled = !useproxy;
	useproxyuser.disabled = !useproxy;


	if (!useproxy)
	{
	        proxypassword.disabled = !useproxy;
		proxyuser.disabled = !useproxy;
	}
	else
	{
		proxyAuthClicked();
	}
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

	var useproxy = document.getElementById('useproxy').checked;
	var useproxyuser = document.getElementById('useproxyuser').checked;

	var proxyaddress = document.getElementById('proxyaddress').value;
	var proxyport = document.getElementById('proxyport').value;
	var proxyuser = document.getElementById('proxyuser').value;
	var proxypassword = document.getElementById('proxypassword').value;
	var disabletunnel = document.getElementById('disabletunnel').checked ? false: true;



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
		qname: qname,
		useproxy: useproxy,
		useproxyuser: useproxyuser,
		proxyaddress: proxyaddress,
		proxyport: proxyport,
		proxyuser: proxyuser,
		proxypassword: proxypassword,
		disabletunnel: disabletunnel
	};

	fetch('savesettings', {
		method: 'POST',	
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(data)
	})
	.then((response) => {
		if (response.status == 200) {
			if (confirm("Settings saved. You have to reboot for them to take effect. Reboot now?")) {
				fetch('reboot', {
			                method: 'POST',
		                });
			}
		}
		else
		{
			alert("Error saving settings");
		}
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

			var textarea = document.getElementById(logfile + "_area");

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

function uploadArrayBufferRawImage(url, arraybuffer, progress, done)
{
	var formData = new FormData();
	formData.append("firmware_image",
                     new Blob([arraybuffer], {type: "application/octet-stream"}),
                     "quickpi.tar.gz");
	fetch(url, {
		method: 'POST',
		body: formData
	}).then(function(resp)
	{
		console.log("fetch, done");
		return resp.text();
	}).then(function(resptext)
	{
		console.log("Response", resptext);
		done(resptext == "ok");
	});
}


function downloadFile(url, progress, done)
{
	var req = new XMLHttpRequest();

	url = url + "?_=" + new Date().getTime();

	req.open("GET", url, true);
	req.addEventListener("progress", function (evt) {
		console.log("progress");
		if(evt.lengthComputable) {
			var percentComplete = evt.loaded / evt.total;
			progress(percentComplete);
		}
	}, false);

	req.responseType = "arraybuffer";
	req.onreadystatechange = function () {
		if (req.readyState === 4 && req.status === 200) {
			console.log("Download finnished");
			var arrayBuffer = req.response; 

			done(arrayBuffer);
		}
	};

	req.onload = function(oEvent) {
		var arrayBuffer = req.response;

		console.log("Download actually finnished");

		console.log(arrayBuffer);

	}

	req.send()
}

function update_now()
{
	var textarea = document.getElementById("update_area");
	var button = document.getElementById("updatebutton");
	var version = 0;

	button.disabled = true;
	textarea.value = "Checking for updates...";

	downloadFile("https://quick-pi.org/update/version",  function(percent) {
	}, function(arrayBuffer) {
		var version = new TextDecoder().decode(arrayBuffer);

		console.log ("Available version " + version);
		textarea.value += "\nDownloading update..." ;

	        downloadFile("https://quick-pi.org/update/quickpi.tar.gz",  function(percent) {

        	        //textarea.value = "Downloading update..." ;

	        }, function(arrayBuffer) {
	                textarea.value += "\nDownloaded update";
			textarea.value += "\nUploading update image to Raspberry Pi (this may take a long time)...\n";

	                uploadArrayBufferRawImage("/api/v1/update_image", arrayBuffer, null, function(status) {
				if (!status) {
					textarea.value += "\nUpdate failed";
					button.disabled = false;
				}
				else
				{
					console.log("Connecting to update ws");
				        var ws = new WebSocket(location.origin.replace(/^http/, 'ws') + "/api/v1/update")

					ws.onopen = function(event) {
						console.log("connecting sending version");
						ws.send(version);
					};

				        ws.onmessage = function(event) {
				                textarea.value += event.data;
				        };

				        ws.onclose = function(event) {
				                button.disabled = false;
				        };

				        ws.onerror = function(error) {
				                textarea.value += "Error: " + error.message
				        };
				}
			});
	        });

	});
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

	        document.getElementById('sn').value = myJson.STATICMASK;

	        document.getElementById('gw').value = myJson.STATICGATEWAY;
	        document.getElementById('ns').value = myJson.STATICDNS;
	        document.getElementById('bluetooth').checked = myJson.ENABLEBLUETOOTH == "1" ? true : false;

        	document.getElementById('school').value = myJson.SCHOOL;
	        document.getElementById('qname').value = myJson.NAME;

		document.getElementById('useproxy').checked = myJson.USEPROXY == "1" ? true : false;
		document.getElementById('useproxyuser').checked = myJson.USEPROXYUSER == "1" ? true : false;

		document.getElementById('proxyaddress').value = myJson.PROXYADDRESS;
		document.getElementById('proxyport').value = myJson.PROXYPORT;
		document.getElementById('proxyuser').value = myJson.PROXYUSER;

		if (typeof(myJson.DISABLETUNNEL) !== "undefined")
			document.getElementById('disabletunnel').checked = myJson.DISABLETUNNEL == "0" ? true : false;
		else
			document.getElementById('disabletunnel').checked = true;


		document.getElementById('wifimac').innerText = myJson.WIFIMAC;
		document.getElementById('ethmac').innerText = myJson.ETHMAC;


		staticIpClicked();
		proxyClicked();

		//document.getElementById('proxypass').value = myJson.;




            });

	openTab(event, 'config');
}
