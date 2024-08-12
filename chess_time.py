import pygame


class Time:
    def __init__(self, mins, increment):
        self.white_time = mins * 60
        self.black_time = mins * 60
        self.increment = increment
        self.start_time = pygame.time.get_ticks()

    def update_start_time(self):
        self.start_time = pygame.time.get_ticks()

    def update_time(self, ticks, turn):
        if turn == "w":
            self.white_time = self.white_time - (ticks - self.start_time)/1000
        else:
            self.black_time = self.black_time - (ticks - self.start_time)/1000

        if self.white_time <= 0:
            self.white_time = 0
        if self.black_time <= 0:
            self.black_time = 0

    def update_increment(self, turn):
        if turn == "w":
            self.black_time = self.black_time + self.increment
        else:
            self.white_time = self.white_time + self.increment