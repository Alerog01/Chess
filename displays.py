import pygame
import move
from board import Board
import constants as cts
import pieces

pygame.init()
pygame.font.init()


class Displays:
    def __init__(self, fen = cts.initial_pos):
        self.board = Board(fen)
        self.promotion_rects = []
        self.promotion = False

    def draw_board(self, dark_color, light_color, screen):
        screen.fill(light_color)

        for i in range(32):
            column = i % 4
            row = i // 4
            if row % 2 == 0:
                pygame.draw.rect(screen, dark_color,
                                 [cts.sqr_side + column * 2 * cts.sqr_side,
                                  row * cts.sqr_side, cts.sqr_side, cts.sqr_side])
            else:
                pygame.draw.rect(screen, dark_color,
                                 [column * 2 * cts.sqr_side,
                                  row * cts.sqr_side, cts.sqr_side, cts.sqr_side])

        pygame.draw.rect(screen, cts.dark_brown, [cts.height, 0,
                                                  20, cts.height])

        pygame.draw.rect(screen, cts.brown_red, [cts.height+ 20, 0,
                                                  180, cts.height])

    def draw_clocks(self, screen, clock):
        font = pygame.font.Font(None, 60)

        white_time = clock.white_time
        black_time = clock.black_time
        white_minutes, white_seconds = divmod(white_time, 60)
        black_minutes, black_seconds = divmod(black_time, 60)

        white_time_text = f'{int(white_minutes):02}:{int(white_seconds):02}'
        black_time_text = f'{int(black_minutes):02}:{int(black_seconds):02}'

        white_label = font.render(f'{white_time_text}', True, pygame.Color('white'))
        black_label = font.render(f'{black_time_text}', True, pygame.Color('black'))

        white_rect = white_label.get_rect(center = (910, 650))
        black_rect = black_label.get_rect(center = (910, 150))

        screen.blit(white_label, white_rect)
        screen.blit(black_label, black_rect)

    def draw_attacked_squares(self, color, screen):
        if color == "b":
            squares = self.board.b_attacked_squares
        else:
            squares = self.board.w_attacked_squares

        for move in squares:
            center = (move[1] * cts.sqr_side + cts.sqr_side / 2, move[0] * cts.sqr_side + cts.sqr_side / 2)
            rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
            rect.center = center

            #implementar suma de tuplas
            dest1, dest2 = move
            if (dest1 + dest2) % 2 != 0:
                pygame.draw.rect(screen, (199, 81, 80), rect)
            else:
                pygame.draw.rect(screen, (255, 204, 203), rect)

    def draw_possible_moves(self, pos, screen, moves):

        for move in moves:
            center = (move[1] * cts.sqr_side + cts.sqr_side / 2, move[0] * cts.sqr_side + cts.sqr_side / 2)
            rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
            rect.center = center

            #implementar suma de tuplas
            dest1, dest2 = move
            if (dest1 + dest2) % 2 != 0:
                pygame.draw.rect(screen, cts.light_dark_brown, rect)
            else:
                pygame.draw.rect(screen, cts.light_yellow, rect)

            #volvemos a dibujar las piezas que esten bajo el rango de ataque de la pieza que movamos,
            #para que no queden por debajo del rectangulo que indica los movimientos posibles
            if not self.board.squares[move[0]][move[1]].isempty():
                target_piece = self.board.squares[move[0]][move[1]].piece
                piece_img = target_piece.get_texture()
                screen.blit(piece_img, rect)

    def draw_pieces(self, screen, mouse_moving, mouse_pos):

        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if self.board.squares[row][col].isempty():
                    pass
                else:
                    if mouse_moving and mouse_pos == (row, col):
                        pass
                    else:
                        piece = self.board.squares[row][col].piece
                        piece_img = piece.get_texture()

                        rect_center = (self.board.squares[row][col].column * cts.sqr_side + cts.sqr_side / 2,
                                       self.board.squares[row][col].row * cts.sqr_side + cts.sqr_side / 2)
                        rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
                        rect.center = (rect_center)

                        screen.blit(piece_img, rect)

    def draw_promotion(self, color, pos, screen):
        rect = pygame.Rect(0, 0, cts.sqr_side, 4 * cts.sqr_side)
        row, col = pos

        if col <= 3:
            if color == "b":
                rect.bottomleft = (cts.sqr_side * (1 + col), 8 * cts.sqr_side)
            else:
                rect.topleft = (cts.sqr_side * (1 + col), 0)
        else:
            if color == "b":
                rect.bottomright = (cts.sqr_side * col, 8 * cts.sqr_side)
            else:
                rect.topright = (cts.sqr_side * col, 0)

        queen = pieces.Queen(color)
        knight = pieces.Knight(color)
        rook = pieces.Rook(color)
        bishop = pieces.Bishop(color)

        new_pieces = [queen, knight, rook, bishop]
        images = []

        for piece in new_pieces:
            images.append(piece.get_texture())

        pygame.draw.rect(screen, cts.light_grey, rect)

        image_rects = []

        if color == "w":
            counter = 0
            for i in range(4):
                image_rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
                image_rect.topleft = tuple([sum(x) for x in zip(rect.topleft, (0, counter * cts.sqr_side))])
                image_rects.append(image_rect)
                counter = counter + 1

            for image, image_rect in zip(images, image_rects):
                screen.blit(image, image_rect)

        if color == "b":
            counter = 0
            for i in range(4):
                image_rect = pygame.Rect(0, 0, cts.sqr_side, cts.sqr_side)
                image_rect.bottomleft = tuple([sum(x) for x in zip(rect.bottomleft, (0, -counter * cts.sqr_side))])
                image_rects.append(image_rect)
                counter = counter + 1

            for image, image_rect in zip(images, image_rects):
                screen.blit(image, image_rect)

        self.promotion_rects = image_rects

    def draw_gameover_screen(self, result, screen):
        font = pygame.font.SysFont("San Francisco", 60)
        if result == "w" or result == "b":
            if result == "w":
                str = "El blanco gana"
            else:
                str = "El negro gana"
            text_screen = font.render(str, True, cts.black)
        else:
            text_screen = font.render("Tablas", True, cts.black)

        rect = pygame.Rect(0,0,4*cts.sqr_side,2*cts.sqr_side)
        rect.center = (400,400)

        waiting = True

        while waiting:
            pygame.draw.rect(screen, cts.dark_grey, rect)
            screen.blit(text_screen, (250, 375))


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYUP:
                    waiting = False
                if event.type == pygame.MOUSEBUTTONUP:
                    waiting = False

            pygame.display.flip()

    def promotion_loop(self, pos, pawn_pos, prom_pos):
        row, col = pos

        piece_list = ["q", "n", "r", "b"]

        counter = 0

        for rect in self.promotion_rects:
            if (col * cts.sqr_side, row * cts.sqr_side) == rect.topleft:
                self.board.move(move.Move(pawn_pos, prom_pos, promotion= piece_list[counter]),
                                self.board.squares[pawn_pos[0]][pawn_pos[1]].piece)
            counter = counter + 1

        self.promotion = False