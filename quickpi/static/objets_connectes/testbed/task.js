function initTask(subTask) {

    subTask.gridInfos = {
        hideSaveOrLoad: false,
        actionDelay: 0,

        includeBlocks: {
            groupByCategory: true,
            generatedBlocks: {
                quickpi: {
                    //     ["turnLedOn", "turnLedOff", "buttonState", "waitForButton", "setLedState", "displayText", "readTemperature", "sleep", "buttonState"]
                    basic: ["turnLedOn", "turnLedOff", "readTemperature", "sleep", "buttonState"],
                    easy: ["setLedState",
                            "waitForButton",
                            "isButtonPressed",
                            "isButtonPressedWithName",
                            "setServoAngle",
                            "readTemperature",
                            "displayText",
                            "displayText2Lines",
                            "buttonWasPressed",
                            "readRotaryAngle", 
                            "turnLedOn", "sleep", 
                            "turnLedOff",
                            "readDistance",
                            "toggleLedState",
                            "readLightIntensity",
                            "currentTime", 
                            "setBuzzerState",
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
                            "computeRotationGyro"
                            ],
                    medium: ["displayText", "waitForButton"],
                    hard: ["readRotaryAngle", "readDistance"],
                }
            },
            standardBlocks: {
                includeAll: true,
                //wholeCategories: ["logic", "loops", "math", "variables"],
                //wholeCategories: ["loops"],
                singleBlocks: {
                    basic: ["controls_if_else"],
                    easy: ["controls_infiniteloop", "logic_boolean", "controls_if_else", "controls_if"],
                    medium: ["controls_whileUntil", "logic_boolean", "controls_if_else", "controls_if"],
                    hard: ["controls_whileUntil", "logic_boolean"]
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

//initWrapper(initTask, null, null);
initWrapper(initTask, ["easy"], "easy", true);

