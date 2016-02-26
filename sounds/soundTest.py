import pygame
import time
pygame.init()
test = pygame.mixer.Sound('A#dim.wav')  #load sound
test.play(-1)

time.sleep(5)


test1 = pygame.mixer.Sound('test3.wav')  #load sound
test1.play(-1)

time.sleep(5)



pygame.quit()

print "end"