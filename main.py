import time
import queue
import pygame
import move
import mouse_movement
import constants as cts
import displays
import sys
import chess_time
import engine
import threading

pygame.init()
pygame.font.init()

row, col = 0, 0

screen = pygame.display.set_mode(cts.size)
drawer = displays.Displays(fen="r1bqkbnr/pppppppp/2n///P/1PPPPPPP/RNBQKBNR w KQkq - 0 1")
engine = engine.Engine()
engine.hash_position(drawer.board)
mouse = mouse_movement.MouseMovement()
time_out = False

against_engine = False
finished = False
best_move = None

def get_engine_move(board):
    board_copy = board.copy()
    engine.get_best_move(board_copy, 4)
    global best_move
    global finished
    best_move = engine.best_move
    finished = True

mins = 5
increment = 2
clock = chess_time.Time(mins, increment)

if against_engine and drawer.board.turn == "b":
    threading.Thread(target=get_engine_move, args=[drawer.board]).start()

while True:
    ticks = pygame.time.get_ticks()
    clock.update_time(ticks, drawer.board.turn)
    start_time = clock.update_start_time()

    if clock.white_time == 0 or clock.black_time == 0:
        time_out = True

    #mirar como arreglar el input de draw board
    drawer.draw_board(cts.colors_dict['Sandcastle']['dark_color'],
                      cts.colors_dict['Sandcastle']['light_color'], screen)
    drawer.draw_clocks(screen, clock)
    #drawer.draw_attacked_squares("b", screen)
    drawer.draw_pieces(screen, mouse.moving, (row, col))

    if finished:
        finished = False
        drawer.board.move(best_move)
        engine.update_hash_after_move(drawer.board)

    if mouse.moving:
        #modificar draw possible moves para poder meter el color
        drawer.draw_possible_moves((row, col), screen, moves_landing)
        mouse.update_draw((mouse.mouse_x, mouse.mouse_y), screen)

    if drawer.promotion:
        drawer.draw_promotion(prom_color, (prom_row, prom_col), screen)

    if drawer.board.checkmate or drawer.board.draw or time_out:
        drawer.draw_board(cts.colors_dict['Sandcastle']['dark_color'],
                          cts.colors_dict['Sandcastle']['light_color'], screen)
        drawer.draw_pieces(screen, mouse.moving, (row, col))

        if drawer.board.checkmate or time_out:
            opp_color = "w" if drawer.board.turn == "b" else "b"
            drawer.draw_gameover_screen(opp_color, screen)
        if drawer.board.draw:
            drawer.draw_gameover_screen("draw", screen)

        drawer.board.draw = False
        drawer.board.checkmate = False
        time_out = False

        en_passant_row, en_passant_col = 0, 0
        turn = "w"
        promotion = False

        drawer = displays.Displays()
        mouse = mouse_movement.MouseMovement()
        clock = chess_time.Time(mins, increment)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print(drawer.board.get_board_fen())
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if drawer.board.turn == "b" and against_engine:
                continue

            mouse.update_pos(event.pos)
            row, col = mouse.get_row_col()

            if drawer.promotion:
                drawer.promotion_loop((row, col), pawn_pos, (prom_row, prom_col))

                drawer.board.check_mate_and_stalemate(drawer.board.turn)

            if mouse.check_click(drawer.board):

                piece = drawer.board.squares[row][col].piece

                if drawer.board.turn != piece.color:
                    continue


                mouse.update_starting_pos(event.pos)
                mouse.start_moving(piece)

                moves = piece.get_legal_moves()
                moves_landing = move.Move.list_to_squares(moves)

        if event.type == pygame.MOUSEMOTION:

            if mouse.moving:
                #las siguientes dos líneas para arreglar bugs visuales
                drawer.draw_board(cts.colors_dict['Sandcastle']['dark_color'],
                                  cts.colors_dict['Sandcastle']['light_color'], screen)
                drawer.draw_pieces(screen, mouse.moving, (row, col))
                drawer.draw_clocks(screen, clock)

                drawer.draw_possible_moves((row, col), screen, moves_landing)
                mouse.update_draw(event.pos, screen)

        if event.type == pygame.MOUSEBUTTONUP:
            if mouse.moving:

                mouse.update_pos(event.pos)
                row, col = mouse.get_row_col()
                starting_row, starting_col = mouse.get_row_col(True)

                if (row, col) in moves_landing:

                    #Coronar
                    if drawer.board.check_promotion((row, col), (starting_row, starting_col)):
                        drawer.promotion = True
                        prom_color = piece.color
                        prom_row, prom_col = row, col
                        pawn_pos = starting_row, starting_col

                    else:
                        drawer.board.move(move.Move((starting_row, starting_col), (row, col)))

                        # repeticiones
                        drawer.board.update_positions_list()
                        if drawer.board.check_repetition_rule():
                            draw = True

                        clock.update_increment(drawer.board.turn)

                        if against_engine and drawer.board.turn == "b" and drawer.board.checkmate == False:
                            engine.update_hash_after_move(drawer.board)
                            threading.Thread(target=get_engine_move, args=[drawer.board]).start()

                else:
                    drawer.board.add_piece(starting_row, starting_col, mouse.piece)

                mouse.stop_moving()

    pygame.display.flip()
