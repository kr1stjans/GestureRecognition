import os
import json


class SaveController:
    @staticmethod
    def save_recorded_gesture(name, gesture, folder_name='gestures'):
        # count number of existing gestures with specified name
        existing_gestures_ctr = 1
        while os.path.isfile(folder_name + "/" + name + "_" + str(existing_gestures_ctr) + ".json"):
            existing_gestures_ctr += 1

        # save new gesture as gesture_name + existing_gestures_ctr + 1
        with open(folder_name + "/" + name + "_" + str(existing_gestures_ctr) + ".json", "w") as output:
            json.dump(gesture, output)
        print "Gesture " + name + "_" + str(existing_gestures_ctr) + " saved.\r"

    @staticmethod
    def load_recorded_gesture(gesture_name, folder_name='gestures'):
        loaded_gestures = []
        # count number of existing gestures with specified name
        existing_gestures_ctr = 1
        while os.path.isfile(folder_name + "/" + gesture_name + "_" + str(existing_gestures_ctr) + ".json"):
            # load every existing gesture into loaded gesture array
            with open(folder_name + "/" + gesture_name + "_" + str(existing_gestures_ctr) + ".json", "r") as output:
                loaded_gestures.append(json.load(output))
            existing_gestures_ctr += 1

        print "Found and loaded " + str(existing_gestures_ctr - 1) + " gestures named " + gesture_name + "\r"
        return loaded_gestures
