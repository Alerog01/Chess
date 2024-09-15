import copy
import board as b
import operator
from abc import ABC, abstractmethod
import pygame
import constants as cts
import square
import itertools
from move import Move

pygame.init()


class Piece(ABC):
    def __init__(self, type, color):
        self.has_moved = False
        self.color = color
        self.opp_color = "w" if self.color == "b" else "b"
        self.type = type
        self.moves = []
        self.short_castling = False
        self.long_castling = False
        self.en_passant = False
        self.attacked_squares = []
        self.legal_moves = []
        self.value = cts.pieces_value[self.type]
        if self.color not in ["b", "w"]:
            raise Exception("Piece color must be either 'b' or 'w'")

    def __eq__(self, other):
        if not isinstance(other, Piece):
            return NotImplemented

        if (self.type == other.type and
                self.color == other.color and
                self.legal_moves == other.legal_moves and
                self.en_passant == other.en_passant):
            return True
        else:
            return False

    def is_sliding(self):
        return False

    def get_legal_moves(self):
        return self.legal_moves

    def set_legal_moves(self, board, pos):

        if self.type == "king":
            valid_moves = self.get_moves(board, pos)
            self.legal_moves = valid_moves
            return

        valid_moves = []

        king_in_check_count, sliding_check, checker_pos = board.w_check_state if self.color == "w" \
            else board.b_check_state
        king_pos = board.w_king_pos if self.color == "w" else board.b_king_pos

        if king_in_check_count == 0:

            if pos in [tup[0] for tup in board.pinned_pieces]:
                if self.type != "knight":

                    for tup in board.pinned_pieces:
                        if pos == tup[0]:
                            pinning_piece_pos = tup[1]
                            break

                    if self.type == "pawn":
                        moves = self.get_moves(board, pos)

                        if board.same_row(pos, pinning_piece_pos):
                            en_passant_pin = False

                            for move in moves:
                                if move.is_passant == True:
                                    en_passant_pin = True

                            if en_passant_pin:
                                for move in moves:
                                    if not move.is_passant:
                                        valid_moves.append(move)

                        if board.same_col(pos, pinning_piece_pos):
                            for move in moves:
                                if board.same_col(move.landing_pos, pinning_piece_pos):
                                    valid_moves.append(move)

                        if board.same_diagonal(pos, pinning_piece_pos):
                            for move in moves:
                                if move.landing_pos == pinning_piece_pos:
                                    valid_moves.append(move)

                    else:
                        king_pos = board.get_king_pos(self.color)
                        distance_to_king = board.distance(pos, king_pos)
                        distance_to_pinning_piece = board.distance(pos, pinning_piece_pos)
                        direction_to_king = board.direction(pos, king_pos)
                        direction_to_pinning_piece = board.direction(pos, pinning_piece_pos)

                        if ((board.same_diagonal(pos, pinning_piece_pos) and self.diag_sliding) or
                           (board.same_row(pos, pinning_piece_pos) and self.hor_ver_sliding) or
                           (board.same_col(pos, pinning_piece_pos) and self.hor_ver_sliding)):
                            set_pin_moves = True
                        else:
                            set_pin_moves = False

                        if set_pin_moves:
                            for offset in range(1, distance_to_king):
                                king_sum_tuple = tuple(map(operator.add, pos, (direction_to_king[0] * -1 * offset,
                                                                               direction_to_king[1] * -1 * offset)))

                                valid_moves.append(Move(pos, king_sum_tuple))

                            for offset in range(1, distance_to_pinning_piece + 1):
                                pinning_sum_tuple = tuple(
                                    map(operator.add, pos, (direction_to_pinning_piece[0] * -1 * offset,
                                                            direction_to_pinning_piece[1] * -1 * offset)))

                                valid_moves.append(Move(pos, pinning_sum_tuple))

                else:
                    valid_moves = []

            else:
                moves = self.get_moves(board, pos)
                valid_moves = moves

        if king_in_check_count == 1:
            if pos in [tup[0] for tup in board.pinned_pieces]:
                valid_moves = []
                self.legal_moves = valid_moves
                return

            moves = self.get_moves(board, pos)

            if sliding_check:
                direction = board.direction(king_pos, checker_pos)
                distance = board.distance(king_pos, checker_pos)

                for offset in range(1, distance):
                    # suma de tuplas
                    sum_tuple = tuple(map(operator.add, checker_pos, (direction[0] * offset, direction[1] * offset)))

                    for move in moves:
                        if move.landing_pos == sum_tuple:
                            valid_moves.append(move)

            if board.squares[checker_pos[0]][checker_pos[1]].piece.en_passant:
                if (self.type == "pawn" and
                        (pos == (checker_pos[0], checker_pos[1] + 1) or pos == (
                                checker_pos[0], checker_pos[1] - 1))):
                    for move in moves:
                        if move.is_passant:
                            valid_moves.append(move)

            for move in moves:
                if move.landing_pos == checker_pos:
                    valid_moves.append(move)

        if king_in_check_count >= 2:
            if self.type != "king":
                self.legal_moves = []
                return

        self.legal_moves = valid_moves

    def get_moves(self, board, pos):
        moves = []
        attacking_moves = self.attacked_squares
        for move in attacking_moves:
            landing_pos = move.landing_pos
            if (board.squares[landing_pos[0]][landing_pos[1]].isempty() or
                    board.squares[landing_pos[0]][landing_pos[1]].piece.color != self.color):
                moves.append(move)

        return moves

    def set_attacked_squares(self, board, pos):
        pass

    def get_attacked_squares(self):
        attacked_squares = Move.list_to_squares(self.attacked_squares)
        return attacked_squares

    def get_texture(self):
        path = "pieces-basic-svg/" + self.type + "-" + self.color + ".svg"
        return pygame.transform.scale(pygame.image.load(path), (cts.sqr_side, cts.sqr_side))

    def __del__(self):
        print()

    def __str__(self):
        return self.type


class Pawn(Piece):
    def __init__(self, color, en_passant=False):
        super().__init__("pawn", color)
        self.en_passant = en_passant
        if self.color == "w":
            self.dir = -1
        else:
            self.dir = 1

    def set_en_passant(self, boolean):
        self.en_passant = boolean

    def get_moves(self, board, pos):
        moves = []
        row, col = pos
        promotion_pieces = ['q', 'n', 'r', 'b']

        if pos[0] == 0 or pos[0] == 7:
            return []

        # movimientos hacia adelante
        if board.squares[row + 1 * self.dir][col].isempty():
            if row + 1 * self.dir == 0 or row + 1 * self.dir == 7:
                for piece in promotion_pieces:
                    moves.append(Move(pos, (row + 1 * self.dir, col), promotion=piece))
            else:
                moves.append(Move(pos, (row + 1 * self.dir, col)))

            if square.Square.in_range(row + 2 * self.dir):
                if self.color == "w" and row == 6 and board.squares[row + 2 * self.dir][col].isempty():
                    moves.append(Move(pos, (row + 2 * self.dir, col)))

                if self.color == "b" and row == 1 and board.squares[row + 2 * self.dir][col].isempty():
                    moves.append(Move(pos, (row + 2 * self.dir, col)))

        # capturas
        offsets = [1, -1]
        for offset in offsets:
            if square.Square.in_range(col + offset):
                if not board.squares[row + 1 * self.dir][col + offset].isempty():
                    if board.squares[row + 1 * self.dir][col + offset].piece.color != self.color:
                        if row + 1 * self.dir == 0 or row + 1 * self.dir == 7:
                            for piece in promotion_pieces:
                                moves.append(Move(pos, (row + 1 * self.dir, col + offset),
                                                  is_passant= False, promotion=piece))
                        else:
                            moves.append(Move(pos, (row + 1 * self.dir, col + offset)))

        # al paso
        for offset in offsets:
            if square.Square.in_range(col + offset):
                if not board.squares[row][col + offset].isempty():
                    if (board.squares[row][col + offset].piece.en_passant and
                            board.squares[row][col + offset].piece.color != self.color):
                        moves.append(Move(pos, (row + 1 * self.dir, col + offset), True))

        return moves

    def set_attacked_squares(self, board, pos):
        moves = []
        row, col = pos

        if row == 7 or row == 0:
            self.attacked_squares = []
            return

        offsets = [1, -1]
        for offset in offsets:
            if square.Square.in_range(col + offset):
                moves.append(Move(pos, (row + 1 * self.dir, col + offset)))

        self.attacked_squares = moves


class King(Piece):
    def __init__(self, color):
        super().__init__("king", color)
        self.short_castling = False
        self.long_castling = False
        self.king_moves = self.create_king_moves()

    @staticmethod
    def create_king_moves():
        king_moves = []
        for pair in itertools.product([1, -1, 0], [1, -1, 0]):
            king_moves.append(pair)

        king_moves.remove((0, 0))
        return king_moves

    def in_check(self, board, pos):
        check_count = 0
        sliding_check = False
        piece_pos = None

        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not board.squares[row][col].isempty():
                    if board.squares[row][col].piece.color != self.color:
                        if pos in board.squares[row][col].piece.get_attacked_squares():
                            if board.squares[row][col].piece.is_sliding():
                                sliding_check = True
                            piece_pos = (row, col)
                            check_count = check_count + 1

        return [check_count, sliding_check, piece_pos]

    def get_moves(self, board, pos):
        attacking_moves = self.attacked_squares
        moves = []
        row, col = pos

        if self.color == "w":
            opp_att_squares = board.b_attacked_squares
        else:
            opp_att_squares = board.w_attacked_squares

        for att_move in attacking_moves:

            landing_pos = att_move.landing_pos
            if landing_pos in opp_att_squares:
                continue

            if (board.squares[landing_pos[0]][landing_pos[1]].isempty() or
                    board.squares[landing_pos[0]][landing_pos[1]].piece.color != self.color):
                moves.append(att_move)

        check_count = board.w_check_state[0] if self.color == "w" else board.b_check_state[0]

        if check_count == 0:
            self.set_castling(board, pos, "k")
            if self.short_castling:
                moves.append(Move(pos, (row, col + 2)))

            self.set_castling(board, pos, "q")
            if self.long_castling:
                moves.append(Move(pos, (row, col - 2), ))

        return moves

    def set_castling(self, board, pos, cast_type):
        if self.color == "w":
            fen_rep = cast_type.upper()
        else:
            fen_rep = cast_type

        if fen_rep not in board.castling_rights:
            return

        if self.has_moved:
            if self.color == "w":
                board.castling_rights = board.castling_rights.replace("K", "")
                board.castling_rights = board.castling_rights.replace("Q", "")
            else:
                board.castling_rights = board.castling_rights.replace("k", "")
                board.castling_rights = board.castling_rights.replace("q", "")
            self.short_castling = False
            self.long_castling = False
            return

        row, col = pos
        rook_col = 0 if cast_type == "q" else 7

        if (board.squares[row][rook_col].isempty() or
                board.squares[row][rook_col].piece.type != "rook" or
                board.squares[row][rook_col].piece.has_moved == True):
            if cast_type == "q":
                if self.color == "w":
                    board.castling_rights = board.castling_rights.replace(fen_rep.upper(), "")
                else:
                    board.castling_rights = board.castling_rights.replace(fen_rep, "")
                self.long_castling = False
                return None
            else:
                if self.color == "w":
                    board.castling_rights = board.castling_rights.replace(fen_rep.upper(), "")
                else:
                    board.castling_rights = board.castling_rights.replace(fen_rep, "")
                self.short_castling = False
                return

        if cast_type == "q":
            for in_btw_col in range(1, 4):
                if not board.squares[row][in_btw_col].isempty():
                    self.long_castling = False
                    return
                if in_btw_col != 1:
                    if self.color == "w":
                        if (row, in_btw_col) in board.b_attacked_squares:
                            self.long_castling = False
                            return
                    else:
                        if (row, in_btw_col) in board.w_attacked_squares:
                            self.long_castling = False
                            return
                if in_btw_col == 3:
                    self.long_castling = True
        if cast_type == "k":
            for in_btw_col in range(1, 3):
                if not board.squares[row][col + in_btw_col].isempty():
                    self.short_castling = False
                    return
                if self.color == "w":
                    if (row, col + in_btw_col) in board.b_attacked_squares:
                        self.short_castling = False
                        return
                else:
                    if (row, col + in_btw_col) in board.w_attacked_squares:
                        self.short_castling = False
                        return
                if in_btw_col == 2:
                    self.short_castling = True

    def set_attacked_squares(self, board, pos):
        moves = []
        row, col = pos

        for move in self.king_moves:
            if square.Square.in_range(row + move[0], col + move[1]):
                moves.append(Move(pos, (row + move[0], col + move[1])))

        self.attacked_squares = moves


class Knight(Piece):
    def __init__(self, color):
        super().__init__("knight", color)
        self.knight_moves = {
            (1, 2),
            (1, -2),
            (-1, 2),
            (-1, -2),
            (2, 1),
            (2, -1),
            (-2, 1),
            (-2, -1)
        }

    def set_attacked_squares(self, board, pos):
        moves = []
        row, col = pos

        for move in self.knight_moves:
            if square.Square.in_range(row + move[0], col + move[1]):
                moves.append(Move(pos, (row + move[0], col + move[1])))

        self.attacked_squares = moves


class SlidingPiece(Piece):
    def __init__(self, type, color):
        self.directions = self.get_directions()
        self.diag_sliding = True
        self.hor_ver_sliding = True
        super().__init__(type, color)

    @abstractmethod
    def get_directions(self):
        pass

    def is_sliding(self):
        return True

    def set_attacked_squares(self, board, pos):
        moves = []
        row, col = pos

        for direction in self.directions:
            counter = 1

            while square.Square.in_range(row + direction[0] * counter, col + direction[1] * counter):
                if board.squares[row + direction[0] * counter][col + direction[1] * counter].isempty():
                    moves.append(Move(pos, (row + direction[0] * counter, col + direction[1] * counter)))
                    counter += 1

                else:
                    if (board.squares[row + direction[0] * counter][
                        col + direction[1] * counter].piece.type == "king" and
                            board.squares[row + direction[0] * counter][
                                col + direction[1] * counter].piece.color != self.color):
                        moves.append(Move(pos, (row + direction[0] * counter, col + direction[1] * counter)))
                        counter += 1

                    else:
                        moves.append(Move(pos, (row + direction[0] * counter, col + direction[1] * counter)))
                        break

        self.attacked_squares = moves


class Queen(SlidingPiece):
    def __init__(self, color):
        super().__init__("queen", color)

    def get_directions(self):
        return King.create_king_moves()


class Rook(SlidingPiece):
    def __init__(self, color):
        super().__init__("rook", color)
        self.hor_ver_sliding = True
        self.diag_sliding = False

    def get_directions(self):
        return [(1, 0), (0, 1), (-1, 0), (0, -1)]


class Bishop(SlidingPiece):
    def __init__(self, color):
        super().__init__("bishop", color)
        self.diag_sliding = True
        self.hor_ver_sliding = False

    def get_directions(self):
        return [(1, 1), (1, -1), (-1, 1), (-1, -1)]
