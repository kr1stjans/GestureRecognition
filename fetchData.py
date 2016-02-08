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

import xmm

PORT = 10337

# 0 is playing
# 1 is recording
# 2 is quit
MODE = 0

PLAYING_QUEUE_SIZE = 600
ABS_Y_AXIS = 250

PLOTTING_FPS = 0.06

# gestures helper
current_gesture = []
recorded_gestures = []

# Gaussian Mixture Model global variables
training_set = xmm.TrainingSet()
training_set.set_dimension(3)  # dimension of data in this example
training_set.set_column_names(xmm.vectors(['x', 'y', 'z']))
gmm = xmm.GMMGroup()
LIKELIHOOD_WINDOW = 5

# HHMM
hhmm = xmm.HierarchicalHMM()

# 0 = no mode, plotting eulers
# 1 = train and plot GMM log likelihoods
# 2 = train and plot HMM
prev_time = time.time()
RECOGNITION_MODE = 0

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
    global MODE, recorded_gestures, RECOGNITION_MODE
    while True:
        input_char = readchar.readchar()
        if input_char.isdigit():
            mode = int(input_char)
            RECOGNITION_MODE = mode
            print "Setting recognition mode: ", RECOGNITION_MODE
        elif input_char == 'r':
            if MODE == 1:
                print "Stopped recording"
                MODE = 0
            else:
                print "Started recording"
                MODE = 1
        elif input_char == 'p':
            MODE = 0
            print "Entered playing mode"
        elif input_char == 't':
            train_model()
        elif input_char == 'q':
            MODE = 2
            print "Quitting"
            sys.exit()


def update_model(eulers):
    if RECOGNITION_MODE == 0:
        euler_queue.append(eulers)
    elif RECOGNITION_MODE == 1:
        gmm.performance_update(xmm.vectorf(eulers))
    elif RECOGNITION_MODE == 2:
        hhmm.performance_update(xmm.vectorf(eulers))


def train_model():
    if RECOGNITION_MODE == 1:
        print "Training Gaussian Mixture Model"
        for i in range(len(recorded_gestures)):
            for frame in recorded_gestures[i]:
                # Append data frame to the phrase i
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(i + 1))
        # Set pointer to the training set
        gmm.set_trainingSet(training_set)

        # Set parameters
        gmm.set_nbMixtureComponents(10)
        gmm.set_varianceOffset(1., 0.01)
        # Train all models
        gmm.train()

        # Set Size of the likelihood Window (samples)
        gmm.set_likelihoodwindow(LIKELIHOOD_WINDOW)
        # Initialize performance phase
        gmm.performance_init()

        print "Number of models: ", gmm.size()

        for label in gmm.models.keys():
            print "Model", label.getInt(), ": trained in ", gmm.models[
                label].trainingNbIterations, "iterations, loglikelihood = ", gmm.models[label].trainingLogLikelihood
    elif RECOGNITION_MODE == 2:
        print "Training HHMM"
        for i in range(len(recorded_gestures)):
            for frame in recorded_gestures[i]:
                # Append data frame to the phrase i
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(i + 1))
        # Set pointer to the training set
        hhmm.set_trainingSet(training_set)

        # Set parameters
        hhmm.set_nbMixtureComponents(10)
        hhmm.set_varianceOffset(1., 0.01)
        # Train all models
        hhmm.train()

        # Set Size of the likelihood Window (samples)
        hhmm.set_likelihoodwindow(1)
        # Initialize performance phase
        hhmm.performance_init()

        print "Number of models: ", hhmm.size()

        for label in hhmm.models.keys():
            print "Model", label.getInt(), ": trained in ", hhmm.models[
                label].trainingNbIterations, "iterations, loglikelihood = ", hhmm.models[label].trainingLogLikelihood


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
                if MODE == 1:
                    # record data to current gesture that will later be saved
                    current_gesture.append(euler_raw[:3])
                elif MODE == 0:
                    # save current gesture and clear it
                    if len(current_gesture) > 0:
                        recorded_gestures.append(np.array(current_gesture))
                        current_gesture = []

                    update_model(euler_raw[:3])
                    #plot()

                elif MODE == 2:
                    break

        except socket.error as e:
            if e[0] != 35:
                print e

    sock.close()
    sys.exit()
