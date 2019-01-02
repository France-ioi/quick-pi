from flask import Flask
from flask import request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/api/v1/executeprogram", methods=['POST'])
def executeProgram():
	print("Executing program")
	os.system("pkill -f userprogram; python3 cleanup.py")

	file = open("userprogram.py", "w")
	file.write(request.data.decode("utf-8"))
	file.close()

	os.system("python3 userprogram.py &")

	return "OK"

@app.route("/api/v1/stopprogram", methods=['POST'])
def stopProgram():
	print("Stopping program")

	os.system("pkill -f userprogram; python3 cleanup.py")

	return "OK"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

