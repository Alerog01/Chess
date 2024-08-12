import constants as cts
import copy
import operator
import move
from move import Move
import pieces as p
from square import Square


class Board:

    def __init__(self, fen=cts.initial_pos):
        self.w_pin_ray_squares = []
        self.b_pin_ray_squares = []
        self.pinned_pieces = []
        self.n_of_legal_moves = 0
        self.squares = [[0 for x in range(cts.board_rows)] for y in range(cts.board_cols)]
        self.w_king_pos = None
        self.b_king_pos = None
        self.w_check_state = [0, False, None]
        self.b_check_state = [0, False, None]
        self.castling_rights = "KQkq"
        self.turn = "w"
        self.en_passant_pos = None
        self.en_passant_target_pos = None
        self.checkmate = False
        self.draw = False
        self.__set_up()
        self.positions = []
        self.move_history = []
        self.__load_pieces_fen(fen)
        self.w_attacked_squares = self.__get_attacked_squares("w")
        self.b_attacked_squares = self.__get_attacked_squares("b")

    fen_dict = {
        "P": lambda: p.Pawn("w"),
        "R": lambda: p.Rook("w"),
        "B": lambda: p.Bishop("w"),
        "Q": lambda: p.Queen("w"),
        "N": lambda: p.Knight("w"),
        "K": lambda: p.King("w"),
        "p": lambda: p.Pawn("b"),
        "q": lambda: p.Queen("b"),
        "n": lambda: p.Knight("b"),
        "k": lambda: p.King("b"),
        "b": lambda: p.Bishop("b"),
        "r": lambda: p.Rook("b")
    }

    def handle_en_passant(self, mouse_pos, starting_pos):
        starting_row, starting_col = starting_pos
        row, col = mouse_pos

        if self.en_passant_pos is not None:
            if not self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].isempty():
                if (self.squares[row][col].piece.type == "pawn" and abs(col - starting_col) == 1
                        and (row, col) == (self.en_passant_target_pos[0], self.en_passant_target_pos[1])):
                    self.delete_piece(self.en_passant_pos[0], self.en_passant_pos[1])

            if (not self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].isempty() and
                    self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece.type == "pawn"):
                self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece.set_en_passant(False)

            self.en_passant_pos = None
            self.en_passant_target_pos = None

        if self.squares[row][col].piece.type == "pawn" and abs(row - starting_row) == 2:
            self.en_passant_target_pos = ((starting_row + row) // 2, col)
            self.en_passant_pos = (row, col)

            self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece.set_en_passant(True)

    def check_promotion(self, landing_pos, starting_pos):
        row, col = landing_pos
        starting_row, starting_col = starting_pos
        if (self.squares[starting_row][starting_col].piece.type == "pawn" and
                (row == (cts.board_rows - 1) or row == 0)):
            return True

    def handle_castling(self, pos, starting_col):
        row, col = pos

        if not self.squares[row][col].piece.has_moved:
            self.squares[row][col].piece.has_moved = True

        if self.squares[row][col].piece.type == "king" and abs(col - starting_col) == 2:
            if col - starting_col < 0:
                self.add_piece(row, col + 1,
                               p.Rook(self.squares[row][col].piece.color))
                self.delete_piece(row, 0)
            if col - starting_col > 0:
                self.add_piece(row, col - 1,
                               p.Rook(self.squares[row][col].piece.color))
                self.delete_piece(row, 7)

    def check_mate_and_stalemate(self):
        check_count = self.w_check_state[0] if self.turn == "w" else self.b_check_state[0]

        if self.n_of_legal_moves == 0:
            if check_count > 0:
                self.checkmate = True
            else:
                self.draw = True

    def distance(self, pos1, pos2):
        row_diff = pos1[0] - pos2[0]
        col_diff = pos1[1] - pos2[1]
        return max([abs(row_diff), abs(col_diff)])

    def direction(self, pos1, pos2):
        if self.same_row(pos1, pos2) == True:
            col_diff = pos1[1] - pos2[1]
            return (0, col_diff // abs(col_diff))
        if self.same_col(pos1, pos2) == True:
            row_diff = pos1[0] - pos2[0]
            return (row_diff // abs(row_diff), 0)
        else:
            row_diff = pos1[0] - pos2[0]
            col_diff = pos1[1] - pos2[1]
            return (row_diff // abs(row_diff), col_diff // abs(col_diff))

    def same_diagonal(self, pos1, pos2):
        row_diff = pos1[0] - pos2[0]
        col_diff = pos1[1] - pos2[1]

        if abs(row_diff) == abs(col_diff):
            return True
        else:
            return False

    def same_row(self, pos1, pos2):
        row_diff = pos1[0] - pos2[0]
        if row_diff == 0:
            return True
        else:
            return False

    def same_col(self, pos1, pos2):
        col_diff = pos1[1] - pos2[1]
        if col_diff == 0:
            return True
        else:
            return False

    def get_king_pos(self, color):
        if color == "w":
            return self.w_king_pos
        if color == "b":
            return self.b_king_pos

    def get_pin_ray_squares(self, color):
        if color == "w":
            return self.w_pin_ray_squares
        else:
            return self.b_pin_ray_squares

    def set_pin_ray_squares(self, color):
        if color == "w":
            self.w_pin_ray_squares = []
        else:
            self.b_pin_ray_squares = []

        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not self.squares[row][col].isempty():
                    if self.squares[row][col].piece.color == color:
                        if self.squares[row][col].piece.is_sliding():
                            enemy_king_pos = self.get_king_pos(self.squares[row][col].piece.opp_color)

                            if (self.same_diagonal((row, col), enemy_king_pos) or
                                    self.same_row((row, col), enemy_king_pos) or
                                    self.same_col((row, col), enemy_king_pos)):
                                if color == "w":
                                    self.w_pin_ray_squares.append((row, col))
                                else:
                                    self.b_pin_ray_squares.append((row, col))

    def update_pinned_pieces(self):
        self.pinned_pieces = []
        colors = ["w", "b"]

        for color in colors:
            opp_color = "w" if color == "b" else "b"
            for pos in self.get_pin_ray_squares(color):

                opp_king_pos = self.get_king_pos(opp_color)
                direction = self.direction(opp_king_pos, pos)

                if not direction in self.squares[pos[0]][pos[1]].piece.get_directions():
                    continue

                distance = self.distance(opp_king_pos, pos)
                n_pieces = 0
                n_pieces_opp_color = 0

                if self.same_row(pos, opp_king_pos) and (opp_king_pos[0] == 3 or opp_king_pos[0] == 4):
                    last_sum_tuple = (0, 0)
                    check_passant = True
                    passant_capture = False
                else:
                    check_passant = False

                for offset in range(1, distance):

                    sum_tuple = tuple(map(operator.add, pos, (direction[0] * offset, direction[1] * offset)))

                    if not self.squares[sum_tuple[0]][sum_tuple[1]].isempty():

                        if self.squares[sum_tuple[0]][sum_tuple[1]].piece.color == opp_color:
                            pinned_piece_pos = sum_tuple
                            n_pieces_opp_color += 1

                        n_pieces += 1

                        if check_passant:
                            if not self.squares[last_sum_tuple[0]][last_sum_tuple[1]].isempty():
                                if ((self.squares[sum_tuple[0]][sum_tuple[1]].piece.en_passant and
                                     self.squares[sum_tuple[0]][sum_tuple[1]].piece.color == color) and
                                        (self.squares[last_sum_tuple[0]][last_sum_tuple[1]].piece.color == opp_color)):
                                    passant_pinned_piece = last_sum_tuple
                                    passant_capture = True

                                if ((self.squares[last_sum_tuple[0]][last_sum_tuple[1]].piece.en_passant and
                                     self.squares[last_sum_tuple[0]][last_sum_tuple[1]].piece.color == color) and
                                        (self.squares[sum_tuple[0]][sum_tuple[1]].piece.color == opp_color and
                                         self.squares[sum_tuple[0]][sum_tuple[1]].piece.type == "pawn")):
                                    passant_pinned_piece = sum_tuple
                                    passant_capture = True

                            if self.squares[sum_tuple[0]][sum_tuple[1]].piece.type == "pawn":
                                last_sum_tuple = sum_tuple

                        if check_passant:
                            if n_pieces > 2:
                                break
                        elif n_pieces > 1:
                            break

                if n_pieces == 1 and n_pieces_opp_color == 1:
                    self.pinned_pieces.append((pinned_piece_pos, pos))

                if check_passant:
                    if n_pieces == 2 and passant_capture:
                        self.pinned_pieces.append((passant_pinned_piece, pos))

    def update_pin_ray_squares(self):
        last_move, last_piece_moved, captured_piece, en_passant_state, castling_state = self.move_history[-1]

        if last_piece_moved.type == "king":
            self.set_pin_ray_squares(last_piece_moved.opp_color)

        if captured_piece != None and captured_piece.is_sliding():
            if captured_piece.color == "w" and last_move.landing_pos in self.w_pin_ray_squares:
                self.w_pin_ray_squares.remove(last_move.landing_pos)
            elif last_move.landing_pos in self.b_pin_ray_squares:
                self.b_pin_ray_squares.remove(last_move.landing_pos)

        if (last_piece_moved.is_sliding() or
                (last_piece_moved.type == "pawn" and last_move.promotion != "" and last_move.promotion != "n")):
            old_pos = last_move.initial_pos
            new_pos = last_move.landing_pos

            if last_piece_moved.color == "w" and old_pos in self.w_pin_ray_squares:
                self.w_pin_ray_squares.remove(old_pos)
            if last_piece_moved.color == "b" and old_pos in self.b_pin_ray_squares:
                self.b_pin_ray_squares.remove(old_pos)

            enemy_king_pos = self.get_king_pos(last_piece_moved.opp_color)

            if (self.same_diagonal(new_pos, enemy_king_pos) or
                    self.same_row(new_pos, enemy_king_pos) or
                    self.same_col(new_pos, enemy_king_pos)):
                if last_piece_moved.color == "w":
                    self.w_pin_ray_squares.append(new_pos)
                else:
                    self.b_pin_ray_squares.append(new_pos)

    def update_positions_list(self):
        self.positions.append(self.get_board_fen())

    def check_repetition_rule(self):
        position = self.get_board_fen()
        counter = self.positions.count(position)
        if counter >= 3:
            return True

    def __set_up(self):
        for x in range(cts.board_rows):
            for y in range(cts.board_cols):
                self.squares[x][y] = Square(x, y)

    def update_legal_moves(self):
        self.n_of_legal_moves = 0
        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not self.squares[row][col].isempty() and self.squares[row][col].piece.color == self.turn:
                    self.squares[row][col].piece.set_legal_moves(self, (row, col))
                    self.n_of_legal_moves += len(self.squares[row][col].piece.legal_moves)

    def __get_attacked_squares(self, color):
        att_squares = set()
        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not self.squares[row][col].isempty():
                    if self.squares[row][col].piece.color == color:
                        att_squares.update(self.squares[row][col].piece.get_attacked_squares())
        return list(att_squares)

    def __update_attacked_squares(self, pos):

        # este tipo de busquedas podria optimizarla teniendo una lista de las piezas del tablero simplemente

        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not self.squares[row][col].isempty():
                    if self.squares[row][col].piece.is_sliding():
                        if pos in self.squares[row][col].piece.get_attacked_squares():
                            self.squares[row][col].piece.set_attacked_squares(self, (row, col))

        self.b_attacked_squares = self.__get_attacked_squares("b")
        self.w_attacked_squares = self.__get_attacked_squares("w")

    def delete_piece(self, row, col):
        self.squares[row][col].piece = None
        self.__update_attacked_squares((row, col))

    def add_piece(self, row, col, piece):

        if piece.type == "king":
            if piece.color == "w":
                self.w_king_pos = (row, col)
            else:
                self.b_king_pos = (row, col)

        self.squares[row][col].piece = piece
        self.squares[row][col].piece.set_attacked_squares(self, (row, col))
        self.__update_attacked_squares((row, col))

    def move(self, move, piece):
        promotion_dict = {
            "q": lambda: p.Queen(piece.color),
            "b": lambda: p.Bishop(piece.color),
            "n": lambda: p.Knight(piece.color),
            "r": lambda: p.Rook(piece.color)
        }

        if not self.squares[move.landing_pos[0]][move.landing_pos[1]].isempty():
            captured_piece = self.squares[move.landing_pos[0]][move.landing_pos[1]].piece
        else:
            if move.is_passant:
                captured_piece = self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece
            else:
                captured_piece = None

        if piece.type == "king" and abs(move.initial_pos[1] - move.landing_pos[1]) == 2:
            castling_move = True
        else:
            castling_move = False

        self.move_history.append((move, piece, captured_piece, (self.en_passant_pos, self.en_passant_target_pos),
                                  (self.castling_rights, piece.has_moved, castling_move)))

        self.delete_piece(move.initial_pos[0], move.initial_pos[1])

        if move.promotion != "":
            self.add_piece(move.landing_pos[0], move.landing_pos[1], promotion_dict[move.promotion]())
        else:
            self.add_piece(move.landing_pos[0], move.landing_pos[1], piece)

        self.handle_castling(move.landing_pos, move.initial_pos[1])
        self.handle_en_passant(move.landing_pos, move.initial_pos)

        self.change_turn()

        if self.turn == "w":
            self.w_check_state = self.squares[self.w_king_pos[0]][self.w_king_pos[1]].piece.in_check(self,
                                                                                                     self.w_king_pos)
        else:
            self.b_check_state = self.squares[self.b_king_pos[0]][self.b_king_pos[1]].piece.in_check(self,
                                                                                                     self.b_king_pos)

        self.update_pin_ray_squares()
        self.update_pinned_pieces()
        self.positions.append(self.get_board_fen())

        self.update_legal_moves()

    def undo_move(self):
        last_move, piece, captured_piece, en_passant_state, castling_state = self.move_history.pop()

        if castling_state[1] == False:
            piece.has_moved = False

        self.castling_rights = castling_state[0]

        castling_move = castling_state[2]

        self.en_passant_pos = en_passant_state[0]
        self.en_passant_target_pos = en_passant_state[1]

        if piece.type == "pawn" and (abs(last_move.initial_pos[0] - last_move.landing_pos[0]) == 2):
            piece.en_passant = False

        self.add_piece(last_move.initial_pos[0], last_move.initial_pos[1], piece)
        self.delete_piece(last_move.landing_pos[0], last_move.landing_pos[1])

        if castling_move:
            if last_move.landing_pos[1] == 6:
                self.add_piece(last_move.landing_pos[0], 7, self.squares[last_move.landing_pos[0]][5].piece)
                self.delete_piece(last_move.landing_pos[0], 5)
            else:
                self.add_piece(last_move.landing_pos[0], 0, self.squares[last_move.landing_pos[0]][3].piece)
                self.delete_piece(last_move.landing_pos[0], 3)

        if captured_piece is not None:
            if last_move.is_passant:
                self.add_piece(self.en_passant_pos[0], self.en_passant_pos[1], captured_piece)
            else:
                self.add_piece(last_move.landing_pos[0], last_move.landing_pos[1], captured_piece)

        if self.en_passant_pos is not None:
            self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece.en_passant = True

        self.change_turn()

        if self.turn == "w":
            self.w_check_state = self.squares[self.w_king_pos[0]][self.w_king_pos[1]].piece.in_check(self,
                                                                                                     self.w_king_pos)
        else:
            self.b_check_state = self.squares[self.b_king_pos[0]][self.b_king_pos[1]].piece.in_check(self,
                                                                                                     self.b_king_pos)

        self.set_pin_ray_squares("w")
        self.set_pin_ray_squares("b")

        self.update_pinned_pieces()
        self.update_legal_moves()

        self.positions.pop()

    def __load_pieces_fen(self, fen):
        fen_list = fen.split(' ')
        board_part = fen_list[0].split("/")

        for i in range(len(board_part)):
            ref = 0
            for j in range(len(board_part[i])):
                if board_part[i][j].isnumeric():
                    ref = ref + int(board_part[i][j])
                else:
                    piece = self.fen_dict[board_part[i][j]]()
                    self.add_piece(i, ref, piece)
                    if self.squares[i][ref].piece.type == "king":
                        if self.squares[i][ref].piece.color == "w":
                            self.w_king_pos = (i, ref)
                        else:
                            self.b_king_pos = (i, ref)

                    piece.set_attacked_squares(self, (i, ref))

                    ref = ref + 1

        self.turn = fen_list[1]

        if "K" not in fen_list[2] and "Q" not in fen_list[2] and "k" not in fen_list[2] and "q" not in fen_list[2]:
            self.en_passant_pos = self.algebraic_to_pos(fen_list[2]) if fen_list[2] != "-" else None
            self.castling_rights = ""
        else:
            self.castling_rights = fen_list[2]
            if "K" not in fen_list[2]:
                self.squares[self.w_king_pos[0]][self.w_king_pos[1]].piece.short_castling = False
            if "Q" not in fen_list[2]:
                self.squares[self.w_king_pos[0]][self.w_king_pos[1]].piece.long_castling = False
            if "k" not in fen_list[2]:
                self.squares[self.b_king_pos[0]][self.b_king_pos[1]].piece.short_castling = False
            if "q" not in fen_list[2]:
                self.squares[self.b_king_pos[0]][self.b_king_pos[1]].piece.long_castling = False

            self.en_passant_pos = self.algebraic_to_pos(fen_list[3]) if fen_list[3] != "-" else None

        if self.en_passant_pos != None:
            self.squares[self.en_passant_pos[0]][self.en_passant_pos[1]].piece.en_passant = True
            if self.en_passant_pos[0] == 3:
                self.en_passant_target_pos = (2, self.en_passant_pos[1])
            else:
                self.en_passant_target_pos = (5, self.en_passant_pos[1])

        self.w_check_state = self.squares[self.w_king_pos[0]][self.w_king_pos[1]].piece.in_check(self, self.w_king_pos)
        self.b_check_state = self.squares[self.b_king_pos[0]][self.b_king_pos[1]].piece.in_check(self, self.b_king_pos)

        self.set_pin_ray_squares("w")
        self.set_pin_ray_squares("b")

        self.update_pinned_pieces()

        self.update_legal_moves()

        self.update_positions_list()
    def get_board_fen(self):
        board_str = ""
        for row in range(cts.board_rows):
            empty_squares = 0
            for col in range(cts.board_cols):
                if self.squares[row][col].isempty():
                    empty_squares += 1
                else:
                    piece = self.squares[row][col].piece
                    if piece.type != "knight":
                        piece_char = piece.type[0]
                    else:
                        piece_char = "n"
                    if empty_squares > 0:
                        board_str += str(empty_squares)
                        empty_squares = 0
                    board_str += piece_char if piece.color == "b" else piece_char.upper()
            if row != 7:
                board_str += "/"

        board_str += " "

        board_str += self.turn

        board_str += " "

        board_str += self.castling_rights

        board_str += " "
        if self.en_passant_pos == None:
            board_str += '-'
        else:
            board_str += self.pos_to_algebraic(self.en_passant_pos)

        board_str += " "

        board_str += "0 1"

        return board_str

    def pos_to_algebraic(self, pos):
        letter = chr(97 + pos[1])
        number = str(cts.board_rows - pos[0])
        return letter + number

    def algebraic_to_pos(self, algebraic):
        letter = algebraic[0]
        number = int(algebraic[1])
        return (cts.board_rows - number, ord(letter) - 97)

    def change_turn(self):
        if self.turn == "w":
            self.turn = "b"
        else:
            self.turn = "w"

    def copy(self):
        return copy.deepcopy(self)
