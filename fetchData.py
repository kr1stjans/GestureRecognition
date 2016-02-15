from threading import Thread
import socket
import struct
import numpy as np
import readchar
import time

import sys
import GesturePlotting as GP

import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

import GaussianMixtureModel as GMM
import HierarchicalHiddenMarkovModel as HHMM


class Mode:
    RECOGNIZING = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    PLOTTING = 3
    QUIT = 4


figure = None
plotter1 = None
plotter2 = None

DEBUG = True
PORT = 10337

recognition_model = None
sound_controller = None
mode = Mode.RECOGNIZING

PLOTTING_QUEUE_SIZE = 400
ABS_Y_AXIS = 200

PLOTTING_FPS = 16.0
plotting_queue = None

# gestures helpers
recorded_gestures = []


# euler_queue = deque([(0, 0, 0) for i in range(0, 600)], PLAYING_QUEUE_SIZE)
# likelihood_log_queue = deque([(0, 0) for _ in range(0, 600)], PLAYING_QUEUE_SIZE)


def unpack_raw(data):
    return struct.unpack(">iiiiiiiii", data[32:-4])


def unpack_eul(data):
    return struct.unpack(">ffff", data[20:])


def unpack_quat(data):
    return struct.unpack(">ffff", data[16:])


def convert_acce_to_units(val):
    return 8.0 * val / 32768.0


def convert_gyro_to_units(val):
    return 2000.0 * val / 28571.4


def convert_compass_to_units(val):
    return 2.0 * val / 25000.0


def read_char():
    global mode, recorded_gestures, recognition_model
    while True:
        input_char = readchar.readchar()
        if input_char == 'r':
            if mode == Mode.RECOGNIZING:
                print "Start recording"
                mode = Mode.START_RECORDING
            elif mode == Mode.START_RECORDING:
                print "Stop recording"
                mode = Mode.STOP_RECORDING
            else:
                raise Exception("Undefined mode")
        elif input_char == 'q':
            mode = Mode.QUIT
            print "Quitting"
            sys.exit()
        elif input_char == 'p':
            mode = Mode.PLOTTING

        if input_char.isdigit():
            if input_char == '1':
                print "Training Gaussian Mixture Model"
                recognition_model = GMM.GaussianMixtureModel(debug=True)
            elif input_char == '2':
                print "Training Hierarchical Hidden Markov Model"
                recognition_model = HHMM.HierarchicalHiddenMarkovModel(debug=True)
            recognition_model.fit(recorded_gestures)


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


def init_plot():
    global figure, plotter1, plotter2
    figure = plt.figure()
    subplot1 = figure.add_subplot(221)
    plt.axis((0, PLOTTING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    plotter1 = GP.GesturePlotting(PLOTTING_QUEUE_SIZE, subplot1, [("r", "a"), ("b", "b"), ("g", "c")])
    plt.legend()

    subplot2 = figure.add_subplot(222)
    plotter2 = GP.GesturePlotting(PLOTTING_QUEUE_SIZE, subplot2, [("b", "a"), ("r", "c")])
    plt.axis((0, PLOTTING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    plt.legend()

    plt.ion()
    plt.show()


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
    # start receiving data in this thread
    while True:
        try:
            # read data if available
            sensor_data, _ = sock.recvfrom(1024)
            if sensor_data[:6] == "/0/eul":
                # data = unpack_raw(sensor_data)[:6]
                # parse euler angles from raw data
                data = unpack_eul(sensor_data)[:3]

                if mode == Mode.RECOGNIZING:
                    if time.time() - prev_time > 1.0 / PLOTTING_FPS and recognition_model is not None:
                        prev_time = time.time()
                        predicted = recognition_model.predict(data)
                        print_array(predicted)
                elif mode == Mode.START_RECORDING:
                    # record data to current gesture that will later be saved
                    current_gesture.append(data)
                elif mode == Mode.STOP_RECORDING:
                    # save current gesture and clear it
                    if len(current_gesture) > 0:
                        # create list of 2D numpy arrays where rows are measurements and columns are attributes
                        recorded_gestures.append(np.array(current_gesture))
                        current_gesture = []
                        mode = Mode.RECOGNIZING
                    else:
                        raise Exception("No data received from the sensor during gesture recording!")
                elif mode == Mode.PLOTTING:
                    plotter1.update_plot(data)
                    plotter2.update_plot(data[:2])
                    if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                        prev_time = time.time()
                        figure.canvas.draw()
                elif mode == Mode.QUIT:
                    break

        except socket.error as e:
            # code 35 = no data ready exception when in non-blocking read
            if e[0] != 35:
                print e

    sock.close()
    sys.exit()
