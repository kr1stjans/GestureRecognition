import math
import time
from Queue import Queue
from collections import OrderedDict
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

# temp_sounds = ["Amaj", "Emaj", "F#min", "Dmaj"]
temp_sounds = ["bass_d", "bass_g", "chord_bm", "chord_f#m", "melody_down", "melody_up"]
direct_gesture_load_names = ["init", "left", "up"]


def print_array(array):
    for f in array:
        print "%1.0f " % f,
    print "\r"


def append_recorded_gestures(recorded_gestures, gestures_group_name, gestures_group):
    """
    :param recorded_gestures:       dictionary where key is gesture group name and value is a list of 2d arrays (gestures)
    :param gestures_group_name:     name of the group of gestures
    :param gestures_group:          list of 2D arrays where rows are measurements and columns are attributes
    :return:
    """
    if gestures_group_name in recorded_gestures:
        recorded_gestures[gestures_group_name].extend(gestures_group)
    else:
        recorded_gestures[gestures_group_name] = gestures_group


if __name__ == "__main__":

    plot_controller = PlotController(1)

    threadsafe_sensor_data_queue = Queue()

    current_gesture = []
    current_gesture_name = None
    recorded_gestures_map = OrderedDict()

    prev_time = 0.0

    # init new sensor data controller thread that will stream received data to specified queue
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

        if current_mode == Mode.START_RECOGNIZING:
            # skip if there is no data
            if current_data is None:
                continue

            # cant recognize without model and sound controller initialized
            if recognition_model is None or sound_controller is None:
                print "You must first train a model, before you start recognizing. Press digit to train a model.\r"
                mode_controller.reset_mode()

            # update model
            recognition_model.update(current_data)
            predicted = recognition_model.normalized_likelihoods()
            best_value = max(predicted)
            best_value_index = math.isnan(best_value)
            if not best_value_index:
                # play sound that is bound to predicted gesture
                sound_controller.play(predicted.index(best_value))
            else:
                print best_value, predicted

            print_array(predicted)

        elif current_mode == Mode.START_RECORDING:
            if current_gesture_name is None:
                print "Can't record without specified gesture name. Specify it by pressing N.\r"
                mode_controller.reset_mode()

            # skip if data is empty
            if current_data is None:
                continue

            # start recording received data by appending it to current gesture array
            current_gesture.append(current_data)

        elif current_mode == Mode.STOP_RECORDING:
            # save current gesture and clear it
            if len(current_gesture) > 0:
                # save gesture to file
                SaveController.save_recorded_gesture(current_gesture_name, current_gesture)

                # append gesture to map. current gesture list must be wrapped into another list
                append_recorded_gestures(recorded_gestures_map, current_gesture_name, [current_gesture])

                # clear current gesture
                current_gesture = []
            else:
                print("No data received from the sensor during gesture recording! Please reboot the sensor.\r")

            mode_controller.reset_mode()

        elif current_mode == Mode.GET_RECORDING_GESTURE_NAME:
            # get gesture name
            current_gesture_name = raw_input("Enter gesture name: ")
            mode_controller.reset_mode()

        elif current_mode == Mode.PLOTTING:
            # cant plot without data
            if current_data is None:
                continue

            # update model with current data
            recognition_model.update(current_data)
            # update subplot
            plot_controller.update_subplot(0, recognition_model.log_likelihoods())

            # redraw if enough time passed
            if time.time() - prev_time > 1.0 / PLOTTING_FPS:
                prev_time = time.time()
                plot_controller.redraw()

        elif current_mode == Mode.LOAD_GESTURE:
            # get gesture name
            name = raw_input("Enter gesture name to load: ")
            # load gestures
            loaded_gestures = SaveController.load_recorded_gesture(name)
            # extended recorded gestures with loaded gestures
            append_recorded_gestures(recorded_gestures_map, name, loaded_gestures)
            # reset mode after gesture loading complete
            mode_controller.reset_mode()

        elif current_mode in TRAINING_MODEL_MODES:
            if current_mode == Mode.HHMM:
                print "Training Hierarchical Hidden Markov Model.\r"
                recognition_model = HierarchicalHiddenMarkovModel()
            elif current_mode == Mode.GMM:
                print "Training Gaussian Mixture Model.\r"
                recognition_model = GaussianMixtureModel()

            # train the model
            recognition_model.train(recorded_gestures_map)
            # print statistics
            recognition_model.print_trained_model_statistics()

            # init sound controller with as much sounds as there is gestures
            sound_controller = SoundC.SoundController(temp_sounds[:len(recorded_gestures_map)])
            # reset mode after training complete
            mode_controller.reset_mode()

        elif current_mode == Mode.QUIT:
            # stop mode controller thread
            mode_controller.stop()
            # stop sensor data controller thread
            sensor_data_controller.stop()
            print "Quit.\r"
            break

        elif current_mode == Mode.IMMEDIATE_GESTURES_LOAD:
            for name in direct_gesture_load_names:
                loaded_gestures = SaveController.load_recorded_gesture(name)
                append_recorded_gestures(recorded_gestures_map, name, loaded_gestures)
            # reset mode after gesture loading complete
            mode_controller.reset_mode()
