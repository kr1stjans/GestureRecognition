class Mode:
    RECOGNIZING = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    PLOTTING = 3
    QUIT = 4
    LOAD_GESTURE = 5
    # models
    HHMM = 6
    GMM = 7
    IMMEDIATE_GESTURES_LOAD = 8


# set of modes where we must not call blocking char read
MODES_WITH_USER_INPUT = {Mode.STOP_RECORDING, Mode.LOAD_GESTURE, Mode.QUIT}

TRAINING_MODEL_MODES = {Mode.HHMM, Mode.GMM}
