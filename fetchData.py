from threading import Thread
import socket
import math
import struct
import numpy as np
import readchar
import time
import SoundController as SoundC
import pickle
import sys
import PlottingController as PlottingC
import SaveController as SaveC
import os.path
from collections import namedtuple

# with brew's python this causes error and plotting doesnt work
# import matplotlib
# matplotlib.use('TkAgg')

import matplotlib.pyplot as plt

import GaussianMixtureModel as GMM
import HierarchicalHiddenMarkovModel as HHMM


class Mode:
    RECOGNIZING = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    PLOTTING = 3
    QUIT = 4
    LOAD_GESTURE = 5


MODES_WITH_USER_INPUT = {Mode.STOP_RECORDING, Mode.LOAD_GESTURE}

figure = None
plotter1 = None
plotter2 = None

DEBUG = True
PORT = 10337

recognition_model = None
sound_controller = None
save_controller = None
mode = Mode.RECOGNIZING

PLOTTING_QUEUE_SIZE = 400
ABS_Y_AXIS = 200

PLOTTING_FPS = 16.0
plotting_queue = None

# gestures helpers
recorded_gestures = []
current_gesture_name = None

temp_sounds = ["DMaj", "GMaj", "BMin", "DMin", "Emin", "FMin"]


def unpack_raw_to_map(data, map):
    unpacked = struct.unpack(">iiiiiiiii", data[32:-4])
    collected_data['raw_acc_x'] = unpacked[0]
    collected_data['raw_acc_y'] = unpacked[1]
    collected_data['raw_acc_z'] = unpacked[2]
    collected_data['raw_rot_x'] = unpacked[3]
    collected_data['raw_rot_y'] = unpacked[4]
    collected_data['raw_rot_z'] = unpacked[5]
    collected_data['raw_mag_x'] = unpacked[6]
    collected_data['raw_mag_y'] = unpacked[7]
    collected_data['raw_mag_z'] = unpacked[8]


def unpack_eul_to_map(data, map):
    unpacked = struct.unpack(">ffff", data[20:])
    collected_data['eul_x'] = unpacked[0]
    collected_data['eul_y'] = unpacked[1]
    collected_data['eul_z'] = unpacked[2]


def unpack_qua_to_map(data, map):
    unpacked = struct.unpack(">ffff", data[16:])
    collected_data['qua_x'] = unpacked[0]
    collected_data['qua_y'] = unpacked[1]
    collected_data['qua_z'] = unpacked[2]


def convert_acce_to_units(val):
    return 8.0 * val / 32768.0


def convert_gyro_to_units(val):
    return 2000.0 * val / 28571.4


def convert_compass_to_units(val):
    return 2.0 * val / 25000.0


def read_char():
    global mode, recorded_gestures, recognition_model, sound_controller, current_gesture_name
    while True:
        # pass if there will be user input (i.e. gesture name) when loading or saving gestures
        if mode in MODES_WITH_USER_INPUT:
            continue

        input_char = readchar.readchar()
        if input_char == 'r':
            if mode == Mode.RECOGNIZING:
                print "Start recording"
                mode = Mode.START_RECORDING
            elif mode == Mode.START_RECORDING:
                print "Stop recording"
                mode = Mode.STOP_RECORDING
            else:
                raise Exception("Undefined mode: " + str(mode))

        elif input_char == 'q':
            mode = Mode.QUIT
            print "Quitting"
            sys.exit()

        elif input_char == 'l':
            mode = Mode.LOAD_GESTURE

        elif input_char == 'p':
            mode = Mode.PLOTTING

        """elif input_char == 'x':
            for name in ["ainit", "bup", "cr"]:
                cnt = 1
                while os.path.isfile(GESTURE_FOLDER + "/" + name + "_" + str(cnt) + ".pkl"):
                    with open(GESTURE_FOLDER + "/" + name + "_" + str(cnt) + ".pkl", "rb") as output:
                        recorded_gestures.append((name, pickle.load(output)))
                    cnt += 1
                print "Found and loaded " + str(cnt - 1) + " gestures named " + name
        """
        """
        elif input_char == 'c':
            sound = pygame.mixer.Sound('sounds/DMaj.wav')
            sound.play()
        elif input_char == 'v':
            sound = pygame.mixer.Sound('sounds/GMaj.wav')
            sound.play()
        elif input_char == 'b':
            sound = pygame.mixer.Sound('sounds/BMin.wav')
            sound.play()
        elif input_char == 'n':
            sound = pygame.mixer.Sound('sounds/DMin.wav')
            sound.play()
        """

        if input_char.isdigit():
            if input_char == '1':
                print "Training Gaussian Mixture Model"
                recognition_model = GMM.GaussianMixtureModel(debug=True)
            elif input_char == '2':
                print "Training Hierarchical Hidden Markov Model"
                recognition_model = HHMM.HierarchicalHiddenMarkovModel(debug=True)
            recognition_model.fit(recorded_gestures)
            sound_controller = SoundC.SoundController(temp_sounds[:len(recorded_gestures)])


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


def init_plot():
    global figure, plotter1, plotter2
    figure = plt.figure()
    subplot1 = figure.add_subplot(221)
    plt.axis((0, PLOTTING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    plotter1 = PlottingC.PlottingController(PLOTTING_QUEUE_SIZE, subplot1,
                                            [("r", "a"), ("b", "b"), ("g", "c")])
    plt.legend()

    plt.ion()
    plt.show()


def init_controllers():
    global save_controller
    save_controller = SaveC.SaveController()


if __name__ == "__main__":
    # start reading console in another thread
    thread = Thread(target=read_char, args=())
    thread.start()

    try:
        # initialize UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # make socket non-blocking
        sock.setblocking(0)
        # bind to localhost
        sock.bind(("0.0.0.0", PORT))
    except Exception as e:
        # print any exception and exit
        print e
        sys.exit()

    current_gesture = []
    prev_time = 0.0

    init_plot()
    init_controllers()

    # start receiving data in this thread
    while True:
        try:
            # read data if available
            sensor_data, _ = sock.recvfrom(1024)

            collected_data = {}

            if sensor_data[:6] == "/0/raw":
                unpack_raw_to_map(sensor_data, collected_data)
            elif sensor_data[:6] == "/0/eul":
                unpack_eul_to_map(sensor_data, collected_data)
            elif sensor_data[:6] == "/0/qua":
                unpack_qua_to_map(sensor_data, collected_data)

            if mode == Mode.RECOGNIZING:
                if time.time() - prev_time > 1.0 / PLOTTING_FPS \
                        and recognition_model is not None \
                        and sound_controller is not None:
                    prev_time = time.time()
                    predicted = recognition_model.predict(data)
                    print_array(predicted)
                    best_value = max(predicted)
                    if not math.isnan(best_value):
                        # play sound bound to predicted gesture
                        sound_controller.play(predicted.index(best_value))
                    else:
                        print best_value, predicted

            elif mode == Mode.START_RECORDING:
                # record data to current gesture that will later be saved
                current_gesture.append(data)

            elif mode == Mode.STOP_RECORDING:
                # save current gesture and clear it
                if len(current_gesture) > 0:
                    # get gesture name
                    current_gesture_name = raw_input("Enter gesture name: ")
                    # save gesture
                    gestureNpArray = np.array(current_gesture)
                    save_controller.save_recorded_gesture(current_gesture_name, gestureNpArray)

                    # append tuple of gesture name and 2D numpy array
                    # where rows are measurements and columns are attributes
                    recorded_gestures.append((current_gesture_name, gestureNpArray))
                    current_gesture = []
                    mode = Mode.RECOGNIZING
                else:
                    raise Exception("No data received from the sensor during gesture recording!")

            elif mode == Mode.PLOTTING:
                plotter1.update_plot(recognition_model.log_likelihoods())
                if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                    prev_time = time.time()
                    figure.canvas.draw()

            elif mode == Mode.LOAD_GESTURE:
                recorded_gestures.extend(save_controller.load_recorded_gesture())
                mode = Mode.RECOGNIZING

            elif mode == Mode.QUIT:
                break

        except socket.error as e:
            # code 35 = no data ready exception when in non-blocking read
            if e[0] != 35:
                print e

    sock.close()
    sys.exit()
