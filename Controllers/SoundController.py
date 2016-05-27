import pygame


class SoundController:
    def __init__(self, sounds):
        self.__sounds = sounds
        self.__last_index = -1
        self.__acc = -1

        pygame.init()

    def __del__(self):
        pygame.quit()

    def play(self, index):
        # 0 is default position with no sound
        if index == 0:
            self.__last_index = index
            return

        if self.__last_index != index:
            self.__last_index = index
            self.__acc = 0
        elif self.__acc >= 80:
            sound = pygame.mixer.Sound("pitch_sounds/" + self.__sounds[index - 1] + ".wav")
            sound.play()
            self.__acc = -1
        elif self.__acc != -1:
            self.__acc += 1
