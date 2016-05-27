import pygame

if __name__ == "__main__":

    pygame.init()
    sound = pygame.mixer.Sound("pitch_sounds/bass_d.wav")
    sound.play()

    while True:
        a = 1
