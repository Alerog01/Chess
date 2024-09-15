import sys

import board
import unittest
import chess
import constants as cts
import constants as cts
import chess_time
import move as m

def get_number_of_moves(test_board, depth):

    if depth == 0:
        return 0

    n_moves = 0

    if depth == 1:
        n_moves += len(test_board.legal_moves)
        return n_moves

    for move in test_board.legal_moves:
        test_board.move(move)

        n_moves += get_number_of_moves(test_board, depth - 1)

        test_board.undo_move()
    return n_moves

def debug_number_of_moves(test_board, depth, chess_board):

    if depth == 0:
        return 0
    n_moves = 0

    for row in range(cts.board_rows):
        for col in range(cts.board_cols):
            if (not test_board.squares[row][col].isempty() and
                    test_board.squares[row][col].piece.color == test_board.turn):

                legal_moves = test_board.squares[row][col].piece.get_legal_moves()

                if depth == 1:
                    n_moves += len(legal_moves)

                    piece_square = chess.square(col, 7 - row)
                    chess_piece_moves = list(chess_board.legal_moves)

                    chess_piece_moves = [move for move in chess_piece_moves if move.from_square == piece_square]
                    n_moves_chess = len(chess_piece_moves)

                    if len(legal_moves) != n_moves_chess:
                        print(test_board.positions)
                        print((test_board.get_board_fen(), row, col, len(legal_moves), n_moves_chess))
                        print(m.Move.list_to_squares(legal_moves), chess_piece_moves)
                        sys.exit()

                    continue

                for move in legal_moves:
                    chess_move = test_board.pos_to_algebraic(move.initial_pos) + test_board.pos_to_algebraic(move.landing_pos)
                    chess_move = chess_move + move.promotion if move.promotion != "" else chess_move
                    chess_move = chess.Move.from_uci(chess_move)

                    chess_board.push(chess_move)
                    test_board.move(move, test_board.squares[row][col].piece)

                    n_moves += debug_number_of_moves(test_board, depth - 1, chess_board)

                    test_board.undo_move()
                    chess_board.pop()

    return n_moves

class test_generation(unittest.TestCase):
        def test_tricky_positions(self):
            for test_position in cts.test_positions:
                depth = test_position["depth"]
                fen = test_position["fen"]
                nodes = test_position["nodes"]

                print(fen)

                my_nodes = get_number_of_moves(board.Board(fen), depth)
                self.assertEqual(my_nodes, nodes)

        def test_tricky_positions_large(self):
            for test_position in cts.test_positions_large:
                depth = test_position["depth"]
                fen = test_position["fen"]
                nodes = test_position["nodes"]

                print(fen)

                my_nodes = get_number_of_moves(board.Board(fen), depth)
                self.assertEqual(nodes, my_nodes)

        def test_debug_positions(self):
            fen = "8/8/1k6/2b5/2pP4/8/5K2/8 b d4 0 1"
            nodes = 1440467
            depth = 6

            my_nodes = debug_number_of_moves(board.Board(fen), depth, chess.Board(fen))
            self.assertEqual(nodes, my_nodes)

        def test_initial_position(self):
            test_board = board.Board()

            nodes = [20, 400, 8902, 197281, 4865609]
            depth = 4
            my_nodes = get_number_of_moves(test_board, depth)
            self.assertEqual(nodes[depth - 1], my_nodes)

if __name__ == '__main__':
    unittest.main()
