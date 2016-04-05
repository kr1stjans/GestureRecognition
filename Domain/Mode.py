class Mode:
    IDLE = -1
    START_RECOGNIZING = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    GET_RECORDING_GESTURE_NAME = 3
    PLOTTING = 4
    QUIT = 5
    LOAD_GESTURE = 6
    # models
    HHMM = 7
    GMM = 8
    IMMEDIATE_GESTURES_LOAD = 9


# set of modes where we must not call blocking char read
MODES_WITH_USER_INPUT = {Mode.LOAD_GESTURE, Mode.GET_RECORDING_GESTURE_NAME, Mode.QUIT}

TRAINING_MODEL_MODES = {Mode.HHMM, Mode.GMM}
