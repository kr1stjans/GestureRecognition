from threading import Thread

import readchar
from Domain.Mode import MODES_WITH_USER_INPUT
from Domain.Mode import Mode


class ModeController(Thread):
    def __init__(self, current_mode=Mode.IDLE):
        super(ModeController, self).__init__()
        self.__read_char = True
        self.__current_mode = current_mode

    def run(self):
        while self.__read_char:
            if self.__current_mode in MODES_WITH_USER_INPUT:
                continue

            pressed_key = readchar.readchar()

            if pressed_key == 'r':
                if self.__current_mode == Mode.IDLE:
                    print "Start recording"
                    self.__current_mode = Mode.START_RECORDING
                elif self.__current_mode == Mode.START_RECORDING:
                    print "Stop recording"
                    self.__current_mode = Mode.STOP_RECORDING
                else:
                    self.reset_mode()
            elif pressed_key == 'i':
                self.__current_mode = Mode.IDLE
            elif pressed_key == 's':
                print "Recognizing\r"
                self.__current_mode = Mode.START_RECOGNIZING
            elif pressed_key == 'q':
                self.__current_mode = Mode.QUIT
            elif pressed_key == 'l':
                self.__current_mode = Mode.LOAD_GESTURE
            elif pressed_key == 'p':
                self.__current_mode = Mode.PLOTTING
            elif pressed_key == '1':
                self.__current_mode = Mode.GMM
            elif pressed_key == '2':
                self.__current_mode = Mode.HHMM
            elif pressed_key == 'm':
                self.__current_mode = Mode.IMMEDIATE_GESTURES_LOAD
            elif pressed_key == 'n':
                self.__current_mode = Mode.GET_RECORDING_GESTURE_NAME

    def stop(self):
        self.__read_char = False

    def get_current_mode(self):
        return self.__current_mode

    def reset_mode(self):
        self.__current_mode = Mode.IDLE
