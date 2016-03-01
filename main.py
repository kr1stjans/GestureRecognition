import math
import time
from Queue import Queue

import numpy as np

from Controllers import SoundController as SoundC
from Controllers.ModeController import ModeController
from Controllers.PlotController import PlotController
from Controllers.SaveController import SaveController
from Controllers.SensorDataController import SensorDataController
from Domain.Mode import Mode
from Domain.Mode import TRAINING_MODEL_MODES
from Models.GaussianMixtureModel import GaussianMixtureModel
from Models.HierarchicalHiddenMarkovModel import HierarchicalHiddenMarkovModel

DEBUG = True

PLOTTING_FPS = 16.0

temp_sounds = ["Amaj", "Emaj", "F#min", "Dmaj"]
direct_gesture_load_names = ["init", "right", "left"]


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


if __name__ == "__main__":

    plot_controller = PlotController(1)

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
            current_data = threadsafe_sensor_data_queue.get()

        if current_mode == Mode.RECOGNIZING:
            # cant recognize without model and sound controller initialized
            if recognition_model is None or sound_controller is None:
                continue

            # cant recognize without data
            if current_data is None:
                continue

            # update model
            recognition_model.update(current_data)
            predicted = recognition_model.normalized_likelihoods()
            best_value = max(predicted)
            best_value_index = math.isnan(best_value)
            if not best_value_index:
                # play sound bound to predicted gesture
                sound_controller.play(predicted.index(best_value))
            else:
                print best_value, predicted

            print_array(predicted)

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
                # convert to numpy array
                np_gestures = np.array(current_gesture)
                # save gesture to file
                SaveController.save_recorded_gesture(current_gesture_name, np_gestures)

                # append tuple of gesture name and 2D numpy array
                # where rows are measurements and columns are attributes
                recorded_gestures.append((current_gesture_name, np_gestures))
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
            predicted_likelihoods = recognition_model.log_likelihoods()

            # update subplot
            plot_controller.update_subplot(0, predicted_likelihoods)

            # redraw if enough time passed
            if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                prev_time = time.time()
                plot_controller.redraw()

        elif current_mode == Mode.LOAD_GESTURE:
            # load gestures
            loaded_gestures = SaveController.load_recorded_gesture_by_name()
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

        elif current_mode == Mode.IMMEDIATE_GESTURES_LOAD:
            for name in direct_gesture_load_names:
                recorded_gestures.extend(SaveController.load_recorded_gesture(name))
            # reset mode after gesture loading complete
            mode_controller.reset_mode()
