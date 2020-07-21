function initTask(subTask) {

    subTask.gridInfos = {
        hideSaveOrLoad: false,
        actionDelay: 0,

        includeBlocks: {
            groupByCategory: true,
            generatedBlocks: {
                quickpi: {
                    easy: ["setLedState",
                            "waitForButton",
                            "isButtonPressed",
                            "isButtonPressedWithName",
                            "setServoAngle",
                            "readTemperature",
                            "displayText",
                            "buttonWasPressed",
                            "readRotaryAngle", 
                            "turnLedOn", "sleep", 
                            "turnLedOff",
                            "readDistance",
                            "toggleLedState",
                            "readLightIntensity",
                            "currentTime", 
                            "setBuzzerState",
                            "setBuzzerNote",
                            "getTemperature", 
                            "drawPoint", 
                            "clearScreen",
                            "drawLine",
                            "drawRectangle",
                            "drawCircle",
                            "fill",
                            "noFill",
                            "stroke",
                            "noStroke",
                            "updateScreen",
                            "autoUpdate",
                            "readAcceleration",
                            "computeRotation",
                            "readSoundLevel",
                            "readMagneticForce",
                            "computeCompassHeading",
                            "readInfraredState",
                            "setInfraredState",
                            "readAngularVelocity",
                            "setGyroZeroAngle",
                            "computeRotationGyro",
                            "setLedBrightness",
                            "getLedBrightness",
                            "isLedOn",
                            "isLedOnWithName",
                            "getServoAngle",
                            "getBuzzerNote",
                            "isBuzzerOnWithName",
                            "turnBuzzerOn",
                            "turnBuzzerOff",
                            "isBuzzerOn",
                            "displayText2Lines",
                            "isPointSet",
			                "connectToCloudStore",
			                "writeToCloudStore",
                            "readFromCloudStore",
                            "readIRMessage",
                            "sendIRMessage",
                            "presetIRMessage",
                            ],
                }
            },
            standardBlocks: {
                includeAll: true,
                //wholeCategories: ["logic", "loops", "math", "variables"],
                //wholeCategories: ["loops"],
                singleBlocks: {
                    easy: ["controls_infiniteloop", "logic_boolean", "controls_if_else", "controls_if"],
                },
            },
        },
        maxIterWithoutAction: 100000,

        customSensors: true,

	runningOnQuickPi: true,

        quickPiSensors: {
            easy: "default",
        },
    };

    subTask.data = {
        easy: [{
            autoGrading: false,
            testName: "Expérimenter",
        }],
    };

    initBlocklySubTask(subTask);
}

displayHelper.avatarType = "none";
displayHelper.timeoutMinutes = 0;
initWrapper(initTask, null, null);
//initWrapper(initTask, ["easy"], "easy", true);

