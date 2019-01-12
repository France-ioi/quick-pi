var pythonLib = "";
var raspiServer = "";
var outputInterval = null;
var wsSession = null;

function updateRPIAddress() {
	var ipaddress = document.getElementById('rpiaddress').value;

	raspiServer = ipaddress + ":5000";
}

function fetchPythonLib(doAfter) {
	fetch('quickpilib.py')
	  .then(function(response) {
		    return response.text();
	  })
	  .then(function(text) {
		pythonLib = text;
		doAfter();
	  });
}

function executeProgram(pythonProgram) {
        if (pythonLib === "") {
                fetchPythonLib(function() { executeProgram(pythonProgram) } );
                return;
        }

        if (wsSession == null) {
                connectoToRPI(function() { executeProgram(pythonProgram) });
                return;
        }

	var fullProgram = pythonLib + pythonProgram;
	var command =
	{
		"command" : "startRunMode",
		"program" : fullProgram
	}

        wsSession.send(JSON.stringify(command));
}

function stopProgram() {
        if (wsSession != null) {
        	var command =
                {
                        "command" : "stopAll",
                }

	        wsSession.send(JSON.stringify(command));

        }
}

function releaseLock()
{
        if (wsSession == null) {
                connectoToRPI(releaseLock);
                return;
        }

	if (wsSession != null) {
                var command =
                {
                        "command" : "close",
                }

		wsSession.send(JSON.stringify(command));
	}
}

function startNewSession()
{
        if (pythonLib === "") {
                fetchPythonLib(startNewSession);
                return;
        }

        if (wsSession == null) {
		connectoToRPI(startNewSession)
                return;
        }

	var command =
        {
        	"command" : "startCommandMode",
		"library" : pythonLib
        }

	wsSession.send(JSON.stringify(command));
}

function connectoToRPI(onConnect)
{
	if (wsSession != null)
	{
		return;
	}

	url = "ws://" + raspiServer + "/api/v1/commands";

	wsSession = new WebSocket(url);

	wsSession.onopen = function() {
                var command =
                {
                        "command" : "grabLock",
                        "username" : getUserName()
                }

                wsSession.send(JSON.stringify(command));


		onConnect();

		setOutput ("New session established\n");
	}

	wsSession.onmessage = function(evt) {
		if (evt.data != "none")
			appendOutput(evt.data + "\n");
	}

	wsSession.onclose = function() {
		wsSession = null;
		appendOutput( "Connection closed\n");
	}
}

function sendCommand(command)
{
	if (wsSession != null) {
	        var command =
                {
                        "command" : "execLine",
                        "line" : command
                }

        	wsSession.send(JSON.stringify(command));

	}
}

function setOutput(string)
{
	var textArea = document.getElementById("programoutput");

	textArea.value = string;
}

function appendOutput(string)
{
	var textArea = document.getElementById("programoutput");

	textArea.value += string;
}

function getUserName()
{
	return document.getElementById("username").value;
}
