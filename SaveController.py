import pickle
import os
import sys


class SaveController:
    def __init__(self, folder_name='gestures'):
        self.__save_folder = folder_name

    def save_recorded_gesture(self, name, gesture):
        cnt = 1
        while os.path.isfile(self.__save_folder + "/" + name + "_" + str(cnt) + ".pkl"):
            cnt += 1

        with open(self.__save_folder + "/" + name + "_" + str(cnt) + ".pkl", "wb") as output:
            pickle.dump(gesture, output)
        print "Gesture " + name + "_" + str(cnt) + " saved."

    def load_recorded_gesture(self):
        loaded_gestures = []

        print "Enter gesture name to load: "
        name = sys.stdin.readline()[:-1]
        cnt = 1
        while os.path.isfile(self.__save_folder + "/" + name + "_" + str(cnt) + ".pkl"):
            with open(self.__save_folder + "/" + name + "_" + str(cnt) + ".pkl", "rb") as output:
                loaded_gestures.append((name, pickle.load(output)))
            cnt += 1
        print "Found and loaded " + str(cnt - 1) + " gestures named " + name
        return loaded_gestures
