import constants as cts
import pygame

pygame.init()


class MouseMovement:
    def __init__(self):
        self.moving = False
        self.piece = None
        self.starting_x = 0
        self.starting_y = 0
        self.mouse_x = 0
        self.mouse_y = 0

    def update_pos(self, pos):
        self.mouse_x, self.mouse_y = pos

    def update_starting_pos(self, pos):
        self.starting_x, self.starting_y = pos

    def update_draw(self, pos, screen):
        self.update_pos(pos)
        texture = self.piece.get_texture()

        rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
        rect.center = pos

        screen.blit(texture, rect)

    def get_row_col(self, starting=False):
        if starting:
            row = self.starting_y // cts.sqr_side
            col = self.starting_x // cts.sqr_side
            return row, col

        row = self.mouse_y // cts.sqr_side
        col = self.mouse_x // cts.sqr_side
        return row, col

    def check_click(self, board):
        row, col = self.get_row_col()
        if board.squares[row][col].isempty():
            return False
        else:
            return True

    def start_moving(self, piece):
        self.moving = True
        self.piece = piece

    def stop_moving(self):
        self.moving = False
        self.piece = None
