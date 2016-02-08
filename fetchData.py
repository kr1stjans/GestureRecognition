from threading import Thread
from collections import deque
import socket
import struct
import numpy as np
import time
import sys
import readchar

import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

import GaussianMixtureModel as GMM
import HierarchicalHiddenMarkovModel as HHMM


class Mode:
    RECOGNIZING = 0
    START_RECORDING = 1
    STOP_RECORDING = 2
    QUIT = 3


DEBUG = True

PORT = 10337

recognition_model = None
mode = Mode.RECOGNIZING

# 0 is playing
# 1 is recording
# 2 is quit

PLAYING_QUEUE_SIZE = 600
ABS_Y_AXIS = 250

PLOTTING_FPS = 0.06

# gestures helpers
current_gesture = []
recorded_gestures = []

prev_time = time.time()

euler_queue = deque([(0, 0, 0) for i in range(0, 600)], PLAYING_QUEUE_SIZE)
likelihood_log_queue = deque([(0, 0) for _ in range(0, 600)], PLAYING_QUEUE_SIZE)


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

        if input_char == '1':
            print "Training Gaussian Mixture Model"
            recognition_model = GMM.GaussianMixtureModel(debug=DEBUG)
        elif input_char == '2':
            print "Training Hierarchical Hidden Markov Model"
            recognition_model = HHMM.HierarchicalHiddenMarkovModel(debug=DEBUG)

        if input_char.isdigit():
            recognition_model.fit(recorded_gestures)


"""
def plot():
    global prev_time

    # draw only every 10th change
    if time.time() - prev_time > PLOTTING_FPS and (
                    (gmm.is_trained() and RECOGNITION_MODE == 1) or RECOGNITION_MODE == 0 or (
                        hhmm.is_trained() and RECOGNITION_MODE == 2)):
        prev_time = time.time()
        if RECOGNITION_MODE == 0:
            subplot_x.set_ydata([a[0] for a in euler_queue])
            subplot_y.set_ydata([a[1] for a in euler_queue])
            subplot_z.set_ydata([a[2] for a in euler_queue])
        elif RECOGNITION_MODE == 1:
            subplot_x.set_ydata([a[0] for a in likelihood_log_queue])
            subplot_y.set_ydata([a[1] for a in likelihood_log_queue])
            array = np.array(gmm.results_log_likelihoods)
            likelihood_log_queue.append((array[0], array[1]))
            print array[0], "\t\t\t", array[1], "\r"
        elif RECOGNITION_MODE == 2:
            # subplot_x.set_ydata([a[0] for a in likelihood_log_queue])
            # subplot_y.set_ydata([a[1] for a in likelihood_log_queue])
            array = np.array(hhmm.results_normalized_likelihoods)
            # likelihood_log_queue.append((array[0], array[1]))
            print "1: %1.0f 2: %1.0f 3: %1.0f 4: %1.0f 5: %1.0f" % tuple(array), "\r"
            # fig1.canvas.draw()
"""


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


if __name__ == "__main__":

    # start reading console in another thread
    thread = Thread(target=read_char, args=())
    thread.start()

    try:
        # prepare sensor connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(("0.0.0.0", PORT))
    except Exception as e:
        print e
        sys.exit()

    fig1 = plt.figure()
    subplot_x = fig1.add_subplot(221)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    subplot_y = fig1.add_subplot(222)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    subplot_z = fig1.add_subplot(223)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))

    # some X and Y data
    x = range(0, PLAYING_QUEUE_SIZE)
    y = [0] * PLAYING_QUEUE_SIZE

    plt.ion()
    subplot_x, = subplot_x.plot(x, y, "-")
    subplot_y, = subplot_y.plot(x, y, "-")
    subplot_z, = subplot_z.plot(x, y, "-")

    # draw and show it
    fig1.canvas.draw()
    plt.show()

    # start receiving data in this thread
    while True:
        try:
            sensor_data, _ = sock.recvfrom(1024)
            if sensor_data[:6] == "/0/eul":
                euler_raw = unpack_eul(sensor_data)
                if mode == Mode.START_RECORDING:
                    # record data to current gesture that will later be saved
                    current_gesture.append(euler_raw[:3])
                elif mode == Mode.STOP_RECORDING:
                    # save current gesture and clear it
                    if len(current_gesture) > 0:
                        recorded_gestures.append(np.array(current_gesture))
                        current_gesture = []
                        mode = Mode.RECOGNIZING
                    else:
                        raise Exception("No data received from the sensor during gesture recording!")
                elif mode == Mode.RECOGNIZING:
                    if time.time() - prev_time > PLOTTING_FPS and recognition_model is not None:
                        prev_time = time.time()
                        predicted_result = recognition_model.predict(euler_raw[:3])
                        print_array(predicted_result)
                elif mode == Mode.QUIT:
                    break

        except socket.error as e:
            if e[0] != 35:
                print e

    sock.close()
    sys.exit()
