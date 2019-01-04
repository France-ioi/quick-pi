var pythonLib = "";
var raspiServer = "";
var outputInterval = null;

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
		if (request.readyState == 4) {
			if (request.status == 423)
				alert("Quick pi is locked by someone else");
		}
	};

	request.send(fullProgram);
}

function stopProgram() {
        url = raspiServer + "/api/v1/stopprogram";

        var request = new XMLHttpRequest();
        request.open('POST', url, true);
        request.onreadystatechange = function() {
                if (request.readyState == 4) {
                        if (request.status == 423)
                                alert("Quick pi is locked by someone else");
                }
        };

        request.send("");
}

function getProgramOutput(outputFunction) {
	url = raspiServer + "/api/v1/readoutput";

        fetch(url)
          .then(function(response) {
                    return response.text();
          })
          .then(function(text) {
		outputFunction(text);
          });
}

function startOutputPoll(textAreaId)
{
	if (outputInterval == null) {
		var textArea = document.getElementById(textAreaId);

		outputInterval = setInterval(function() { getProgramOutput(function(text) { textArea.value = text }) }, 1000)
	}
}

function stopProgramOutput()
{
	if (outputInterval != null)
	{
		clearInterval(outputInterval);
		outputInterval = null;
	}
}

function releaseLock()
{
        url = raspiServer + "/api/v1/releaselock";

        var request = new XMLHttpRequest();
        request.open('POST', url, true);
        request.onreadystatechange = function() {
                if (request.readyState == 4) {
                        if (request.status == 423)
                                alert("Quick pi is locked by someone else");
                }
        };

        request.send("");
}
