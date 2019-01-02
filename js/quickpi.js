var pythonLib = "";
var raspiServer = "";

function updateRPIAddress() {
	var ipaddress = document.getElementById('rpiaddress').value;

	raspiServer = "http://" + ipaddress + ":5000";
}

function fetchPythonLib(doAfter, param) {

	fetch('quickpilib.py')
	  .then(function(response) {
		    return response.text();
	  })
	  .then(function(text) {
		pythonLib = text;
		doAfter(param);
	  });
}

function executeProgram(pythonProgram) {
	// If we don't have our python lib fetch and return to this later
	if (pythonLib === "") {
		fetchPythonLib(executeProgram, pythonProgram);

		return;
	}

	url = raspiServer + "/api/v1/executeprogram";
	var fullProgram = pythonLib + pythonProgram;

	var request = new XMLHttpRequest();
	request.open('POST', url, true);
	request.onreadystatechange = function() {
		if (request.readyState == 4)
			alert("It worked!");
	};

	request.send(fullProgram);
}

function stopProgram() {
        url = raspiServer + "/api/v1/stopprogram";

        var request = new XMLHttpRequest();
        request.open('POST', url, true);
        request.onreadystatechange = function() {
                if (request.readyState == 4)
                        alert("It worked!");
        };

        request.send("");
}

