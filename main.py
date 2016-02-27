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

# with brew's python this causes error and plotting doesnt work
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

    plt.ion()
    figure = plt.figure()
    subplot1 = figure.add_subplot(221)
    plt.axis((0, PLOTTING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    plotter1 = PlottingController(PLOTTING_QUEUE_SIZE, subplot1,
                                  [("r", "a"), ("b", "b"), ("g", "c")])
    plt.legend()
    plt.show()


if __name__ == "__main__":

    init_plot()

    threadsafe_sensor_data_queue = Queue()

    current_gesture = []
    recorded_gestures = []
    prev_time = 0.0

    # init new sensor data controller thread that will stream received data to queue
    sensor_data_controller = SensorDataController(threadsafe_sensor_data_queue)
    sensor_data_controller.start()

    # init new mode controller thread that will read chars and control modes
    mode_controller = ModeController()
    mode_controller.start()

    sound_controller = None
    recognition_model = None

    while True:
        # get current mode
        current_mode = mode_controller.get_current_mode()
        current_data = None

        # consume one queue data if it exists
        if not threadsafe_sensor_data_queue.empty():
            current_data = SensorDataController.get_list_data(threadsafe_sensor_data_queue.get(), "raw")

        if current_mode == Mode.RECOGNIZING:
            # cant recognize without model and sound controller initialized
            if recognition_model is None or sound_controller is None:
                continue

            # cant recognize without data
            if current_data is None:
                continue

            if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                prev_time = time.time()
                recognition_model.update(current_data)
                predicted = recognition_model.normalized_likelihoods()
                print_array(predicted)
                best_value = max(predicted)
                if not math.isnan(best_value):
                    # play sound bound to predicted gesture
                    sound_controller.play(predicted.index(best_value))
                else:
                    print best_value, predicted

        elif current_mode == Mode.START_RECORDING:
            # cant record without data
            if current_data is None:
                continue
            # start recording received data by append it to current gesture array
            current_gesture.append(current_data)

        elif current_mode == Mode.STOP_RECORDING:
            # save current gesture and clear it
            if len(current_gesture) > 0:
                # get gesture name
                current_gesture_name = raw_input("Enter gesture name: ")
                # save gesture
                gestureNpArray = np.array(current_gesture)
                SaveController.save_recorded_gesture(current_gesture_name, gestureNpArray)

                # append tuple of gesture name and 2D numpy array
                # where rows are measurements and columns are attributes
                recorded_gestures.append((current_gesture_name, gestureNpArray))
                current_gesture = []
            else:
                print "No data received from the sensor during gesture recording!"

            mode_controller.reset_mode()

        elif current_mode == Mode.PLOTTING:
            # cant plot without data
            if current_data is None:
                continue

            # update model with current data
            recognition_model.update(current_data)
            # update plot
            plotter1.update_plot(recognition_model.log_likelihoods())
            # redraw if enough time passed
            if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                prev_time = time.time()
                figure.canvas.draw()
                # hack to unfreeze canvas
                plt.pause(0.0001)

        elif current_mode == Mode.LOAD_GESTURE:
            # load gestures
            loaded_gestures = SaveController.load_recorded_gesture()
            # extended recorded gestures with loaded gestures
            recorded_gestures.extend(loaded_gestures)
            # reset mode after gesture loading complete
            mode_controller.reset_mode()

        elif current_mode in TRAINING_MODEL_MODES:
            if current_mode == Mode.HHMM:
                print "Training Hierarchical Hidden Markov Model."
                recognition_model = HierarchicalHiddenMarkovModel()
            elif current_mode == Mode.GMM:
                print "Training Gaussian Mixture Model."
                recognition_model = GaussianMixtureModel()
            recognition_model.train(recorded_gestures)

            # init sound controller with as much sounds as there is gestures
            sound_controller = SoundC.SoundController(temp_sounds[:len(recorded_gestures)])
            # reset mode after training complete
            mode_controller.reset_mode()

        elif current_mode == Mode.QUIT:
            # stop mode controller thread
            mode_controller.stop()
            # stop sensor data controller thread
            sensor_data_controller.stop()
            print "Quit."
            break
