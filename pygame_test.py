import pygame

pygame.mixer.init()
sound = pygame.mixer.Sound("pitch_sounds/chord_bm.wav")
sound.play()
pygame.time.delay(2000)