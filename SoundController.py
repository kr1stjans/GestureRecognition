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
        if index == 0:
            self.__last_index = index
            return

        # 0 is default position with no sound
        if self.__last_index != index:
            self.__last_index = index
            self.__acc = 0
        elif self.__acc >= 2:
            sound = pygame.mixer.Sound("sounds/" + self.__sounds[index - 1] + ".wav")
            sound.play()
            self.__acc = -1
        elif self.__acc != -1:
            self.__acc += 1
