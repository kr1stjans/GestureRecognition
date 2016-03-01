import pickle
import os
import sys


class SaveController:
    @staticmethod
    def save_recorded_gesture(name, gesture, folder_name='gestures'):
        # count number of existing gestures with specified name
        existing_gestures_ctr = 1
        while os.path.isfile(folder_name + "/" + name + "_" + str(existing_gestures_ctr) + ".pkl"):
            existing_gestures_ctr += 1

        # save new gesture as gesture_name + existing_gestures_ctr + 1
        with open(folder_name + "/" + name + "_" + str(existing_gestures_ctr) + ".pkl", "wb") as output:
            pickle.dump(gesture, output)
        print "Gesture " + name + "_" + str(existing_gestures_ctr) + " saved."

    @staticmethod
    def load_recorded_gesture_by_name(folder_name='gestures'):

        print "Enter gesture name to load: "
        name = sys.stdin.readline()[:-1]

        return SaveController.load_recorded_gesture(name)

    @staticmethod
    def load_recorded_gesture(gesture_name, folder_name='gestures'):
        loaded_gestures = []
        # count number of existing gestures with specified name
        existing_gestures_ctr = 1
        while os.path.isfile(folder_name + "/" + gesture_name + "_" + str(existing_gestures_ctr) + ".pkl"):
            # load every existing gesture into loaded gesture array
            with open(folder_name + "/" + gesture_name + "_" + str(existing_gestures_ctr) + ".pkl", "rb") as output:
                loaded_gestures.append((gesture_name, pickle.load(output)))
            existing_gestures_ctr += 1

        print "Found and loaded " + str(existing_gestures_ctr - 1) + " gestures named " + gesture_name
        return loaded_gestures
