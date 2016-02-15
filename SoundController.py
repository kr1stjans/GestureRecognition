import subprocess


class SoundController:
    def __init__(self, sounds):
        self.__sounds = sounds

    def play(self, index):
        subprocess.Popen(["afplay", self.__sounds[index]])
