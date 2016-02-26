import math
import time
from Queue import Queue

import numpy as np
from Domain.Mode import Mode
from Domain.Mode import TRAINING_MODEL_MODES

from Controllers import SoundController as SoundC
from Controllers.ModeController import ModeController
from Controllers.PlottingController import PlottingController
from Controllers.SensorDataController import SensorDataController
from Controllers.SaveController import SaveController
from threading import Thread

# with brew's python this causes error and plotting doesnt work
import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from Models.GaussianMixtureModel import GaussianMixtureModel
from Models.HierarchicalHiddenMarkovModel import HierarchicalHiddenMarkovModel

figure = None
plotter1 = None
plotter2 = None

DEBUG = True

PLOTTING_QUEUE_SIZE = 400
ABS_Y_AXIS = 200

PLOTTING_FPS = 16.0

temp_sounds = ["DMaj", "GMaj", "BMin", "DMin", "Emin", "FMin"]


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


def init_plot():
    global figure, plotter1

    figure = plt.figure()
    subplot1 = figure.add_subplot(221)
    plt.axis((0, PLOTTING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    plotter1 = PlottingController(PLOTTING_QUEUE_SIZE, subplot1,
                                  [("r", "a"), ("b", "b"), ("g", "c")])
    plt.legend()

    plt.ion()
    plt.show()


if __name__ == "__main__":

    #test = Thread(target=init_plot(), args=())
    #test.start()
    #print "works"

    data_queue = Queue()
    current_gesture = []
    prev_time = 0.0

    recorded_gestures = []

    save_controller = SaveController()

    sensor_data_controller = SensorDataController(data_queue)
    sensor_data_controller.start()

    mode_controller = ModeController()
    mode_controller.start()

    sound_controller = None
    recognition_model = None

    while True:
        # get current mode
        current_mode = mode_controller.get_current_mode()
        current_data = None
        # consume queue data
        if not data_queue.empty():
            current_data = SensorDataController.get_list_data(data_queue.get(), "raw")

        if current_mode == Mode.RECOGNIZING:
            if time.time() - prev_time > 1.0 / PLOTTING_FPS \
                    and recognition_model is not None \
                    and sound_controller is not None \
                    and current_data is not None:
                prev_time = time.time()
                predicted = recognition_model.predict(current_data)
                print_array(predicted)
                best_value = max(predicted)
                if not math.isnan(best_value):
                    # play sound bound to predicted gesture
                    sound_controller.play(predicted.index(best_value))
                else:
                    print best_value, predicted

        elif current_mode == Mode.START_RECORDING and current_data is not None:
            # start recording data
            current_gesture.append(current_data)

        elif current_mode == Mode.STOP_RECORDING:
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
            else:
                print "No data received from the sensor during gesture recording!"

            mode_controller.reset_mode()

        elif current_mode == Mode.PLOTTING:
            plotter1.update_plot(recognition_model.log_likelihoods())
            if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                prev_time = time.time()
                figure.canvas.draw()

        elif current_mode == Mode.LOAD_GESTURE:
            recorded_gestures.extend(save_controller.load_recorded_gesture())
            mode_controller.reset_mode()

        elif current_mode in TRAINING_MODEL_MODES:
            if current_mode == Mode.HHMM:
                print "Training Hierarchical Hidden Markov Model"
                recognition_model = HierarchicalHiddenMarkovModel(debug=DEBUG)
            elif current_mode == Mode.GMM:
                print "Training Gaussian Mixture Model"
                recognition_model = GaussianMixtureModel(debug=DEBUG)
            recognition_model.fit(recorded_gestures)
            sound_controller = SoundC.SoundController(temp_sounds[:len(recorded_gestures)])
            mode_controller.reset_mode()

        elif current_mode == Mode.QUIT:
            print "Quitting"
            # stop threads
            mode_controller.stop()
            sensor_data_controller.stop()
            break
