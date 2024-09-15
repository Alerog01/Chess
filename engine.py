import operator
import random
import time
import move
import pieces as p
from math import inf
import square
import board
import bitstring
import constants as cts

class Engine:
    def __init__(self, max_time = 30):
        self.itering = False
        self.max_time = max_time
        self.best_move = None
        self.eval = 0
        self.R = 3
        self.init_hash_table()
        self.transpositions_table= {}


    def is_check(self, move, board):
        if move.null:
            return False

        check = False
        capture = move.is_capture(board)

        moving_piece = board.squares[move.initial_pos[0]][move.initial_pos[1]].piece

        promotion_dict = {
            "q": lambda: p.Queen(moving_piece.color),
            "b": lambda: p.Bishop(moving_piece.color),
            "n": lambda: p.Knight(moving_piece.color),
            "r": lambda: p.Rook(moving_piece.color)
        }

        if move.is_passant:
            captured_piece = board.squares[board.en_passant_target_pos[0]][board.en_passant_target_pos[1]].piece
            board.delete_piece(board.en_passant_target_pos)
        elif capture:
            captured_piece = board.squares[move.landing_pos[0]][move.landing_pos[1]].piece

        if move.promotion != "":
            board.add_piece(move.landing_pos[0], move.landing_pos[1],
                            promotion_dict[move.promotion](), simulation=True)
        else:
            board.add_piece(move.landing_pos[0], move.landing_pos[1],
                            board.squares[move.initial_pos[0]][move.initial_pos[1]].piece, simulation=True)

        board.delete_piece(move.initial_pos[0], move.initial_pos[1], simulation=True)

        board.squares[move.landing_pos[0]][move.landing_pos[1]].piece.set_attacked_squares(board, move.landing_pos)
        attacks_from_landing = board.squares[move.landing_pos[0]][move.landing_pos[1]].piece.get_attacked_squares()

        opp_king_pos = board.get_king_pos(moving_piece.opp_color)

        if opp_king_pos in attacks_from_landing:
            check = True

        pin_ray_squares = board.get_pin_ray_squares(moving_piece.color)

        for square in pin_ray_squares:
            if move.initial_pos == square:
                continue
            if (board.same_col(opp_king_pos, square) and board.same_col(move.initial_pos, square) or
                    board.same_row(opp_king_pos, square) and board.same_row(move.initial_pos, square) or
                    board.same_diagonal(opp_king_pos, square) and board.same_diagonal(move.initial_pos, square)):
                board.squares[square[0]][square[1]].piece.set_attacked_squares(board, square)
                if opp_king_pos in board.squares[square[0]][square[1]].piece.get_attacked_squares():
                    check = True

        board.delete_piece(move.landing_pos[0], move.landing_pos[1], simulation=True)

        if move.is_passant:
            board.add_piece(board.en_passant_target_pos[0], board.en_passant_target_pos[1], captured_piece, True)
        elif capture:
            board.add_piece(move.landing_pos[0], move.landing_pos[1], captured_piece, True)

        board.add_piece(move.initial_pos[0], move.initial_pos[1], moving_piece, simulation=True)

        board.squares[move.initial_pos[0]][move.initial_pos[1]].piece.set_attacked_squares(board, move.initial_pos)
        for square in pin_ray_squares:
            board.squares[square[0]][square[1]].piece.set_attacked_squares(board, square)

        return check

    #Necesario para el see. Revisar
    def get_attackers(self, square, board, color):
        attackers = []
        if color == "w":
            pos_types = [x.upper() for x in cts.piece_types]
        else:
            pos_types = cts.piece_types

        for pos_type in pos_types:
            new_piece = board.fen_dict[pos_type]()
            new_piece.set_attacked_squares(board, square)
            attacked_squares = new_piece.get_attacked_squares()
            for att_square in attacked_squares:
                if (not board.squares[att_square[0]][att_square[1]].isempty() and
                        board.squares[att_square[0]][att_square[1]].piece.color != color and
                        board.squares[att_square[0]][att_square[1]].piece.type == new_piece.type):
                    attackers.append((att_square, board.squares[att_square[0]][att_square[1]].piece.value))

        return attackers

    def update_attackers(self, pos, board, attacker_square):
        if board.squares[attacker_square[0]][attacker_square[1]].piece.is_sliding():
            direction = board.direction(pos, attacker_square)
            offset = -1
            sum_tuple = tuple(map(operator.add, attacker_square, (direction[0] * offset, direction[1] * offset)))

            while square.Square.in_range(sum_tuple[0], sum_tuple[1]):
                if not board.squares[sum_tuple[0]][sum_tuple[1]].isempty():
                    if board.squares[sum_tuple[0]][sum_tuple[1]].piece.is_sliding():
                        if board.same_diagonal(attacker_square, pos):
                            if board.squares[sum_tuple[0]][sum_tuple[1]].piece.diag_sliding:
                                return sum_tuple, board.squares[sum_tuple[0]][sum_tuple[1]].piece.value

                        if board.same_col(attacker_square, pos) or board.same_row(attacker_square, pos):
                            if board.squares[sum_tuple[0]][sum_tuple[1]].piece.hor_ver_sliding:
                                return sum_tuple, board.squares[sum_tuple[0]][sum_tuple[1]].piece.value
                offset -= 1
                sum_tuple = tuple(map(operator.add, attacker_square, (direction[0] * offset, direction[1] * offset)))

        return []

    #implementar lo del rey y tener en cuenta que si en algun momento la captura nos beenficia podemos parar
    def see(self, move, board):
        scores_after_defender_move = []
        attacked_value = cts.pieces_value[board.squares[move.landing_pos[0]][move.landing_pos[1]].piece.type]
        attacker_value = cts.pieces_value[board.squares[move.initial_pos[0]][move.initial_pos[1]].piece.type]

        attackers = self.get_attackers(move.landing_pos, board,
                                       board.squares[move.initial_pos[0]][move.initial_pos[1]].piece.opp_color)

        defenders = self.get_attackers(move.landing_pos, board,
                                       board.squares[move.initial_pos[0]][move.initial_pos[1]].piece.color)

        for attacker in attackers:
            if attacker[0] == move.initial_pos:
                attackers.remove(attacker)

        score = attacked_value
        attacked_value = attacker_value
        new_attacker = self.update_attackers(move.landing_pos, board, move.initial_pos)
        turn = -1

        if not defenders:
            return score

        if new_attacker:
            attackers.append(new_attacker)

        attackers.sort(reverse = True, key = lambda att_tup: att_tup[1])
        defenders.sort(reverse = True, key = lambda def_tup: def_tup[1])

        while turn == 1 and attackers != [] or turn == -1 and defenders != []:
            if turn == -1:
                defender_sq, value = defenders.pop()
                score = score - attacked_value
                scores_after_defender_move.append(score)
                attacked_value = value
                new_defender = self.update_attackers(move.landing_pos, board, defender_sq)

                if new_defender:
                    defenders.append(new_defender)
                    defenders.sort(reverse=True, key=lambda def_tup: def_tup[1])

            else:
                attacker_sq, value = attackers.pop()
                score = score + attacked_value
                attacked_value = value
                new_attacker = self.update_attackers(move.landing_pos, board, attacker_sq)

                if new_attacker:
                    attackers.append(new_attacker)
                    attackers.sort(reverse=True, key=lambda att_tup: att_tup[1])

            turn = turn * -1

        score = max(scores_after_defender_move)

        return score

    def order_captures(self, eval_board, captures):
        captures.sort(reverse=True, key = lambda capture: self.see(capture, eval_board))
        return captures

    def get_ordered_moves(self, eval_board, null_move):
        moves = eval_board.get_all_moves()
        ordered_moves = []
        last_moves_ind = []
        capture_moves_ind = []

        hash_move = None

        if self.z_hash in self.transpositions_table:
            hash_move = self.transpositions_table[self.z_hash]["best_move"]

            if hash_move is not None and not hash_move.null:
                ordered_moves.append(hash_move)

        if self.check_null_move_conditions(eval_board) and null_move:
            ordered_moves.append(move.Move((0,0), (0,0), null_move=True))

        for i in range(len(moves)):
            if moves[i] == hash_move or moves[i] == self.best_move:
                continue
            if moves[i].is_capture(eval_board):
                capture_moves_ind.append(i)
            else:
                last_moves_ind.append(i)

        capture_moves = [moves[i] for i in capture_moves_ind]
        sorted_captures = self.order_captures(eval_board, capture_moves)

        ordered_moves.extend(sorted_captures)
        ordered_moves.extend([moves[i] for i in last_moves_ind])

        return ordered_moves

    def material_sum(self, eval_board):
        material_score = 0
        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not eval_board.squares[row][col].isempty():
                    piece = eval_board.squares[row][col].piece
                    if piece.color == "w":
                        color_mult = 1
                    else:
                        color_mult = -1
                    material_score = material_score + eval_board.squares[row][col].piece.value * color_mult

        return material_score

    def is_endgame(self, eval_board):
        w_has_queen = eval_board.has_queen("w")
        b_has_queen = eval_board.has_queen("b")

        if not w_has_queen and not b_has_queen:
            return True

        w_minor_piece_count = eval_board.minor_piece_value_count("w")
        b_minor_piece_count = eval_board.minor_piece_value_count("b")

        if w_has_queen and w_minor_piece_count > 400:
            return False

        if b_has_queen and b_minor_piece_count > 400:
            return False

        return True

    def eval_ps_table(self, eval_board):
        endgame = self.is_endgame(eval_board)
        if endgame:
            stage = "eg"
        else:
            stage = "mg"

        ps_score = 0

        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not eval_board.squares[row][col].isempty():
                    if eval_board.squares[row][col].piece.type == "king":
                        if eval_board.squares[row][col].piece.color == "w":
                            ps_score = ps_score + cts.piece_square_tables_simple["king"][stage][row][col]
                        else:
                            ps_score = ps_score - cts.piece_square_tables_simple["king"][stage][7 - row][col]
                    else:
                        piece_type = eval_board.squares[row][col].piece.type
                        if eval_board.squares[row][col].piece.color == "w":
                            ps_score = ps_score + cts.piece_square_tables_simple[piece_type]["mg"][row][col]
                        else:
                            ps_score = ps_score - cts.piece_square_tables_simple[piece_type]["mg"][7 - row][col]

        return ps_score

    def position_eval(self,eval_board):
        material_score = self.material_sum(eval_board) + self.eval_ps_table(eval_board)
        return material_score / 100

    def alpha_beta_pruning_nm(self, search_board, depth, alpha=-inf, beta=inf, add_null_move = True, reduction = True):
        n_nodes = 0

        if search_board.checkmate:
            evaluation = 10000 if search_board.turn == "b" else -10000
            return {"eval": evaluation, "best_move": None, "n_nodes": n_nodes}

        iteration_hash = self.z_hash

        if iteration_hash in self.transpositions_table:
            stored_value = self.transpositions_table[iteration_hash]

            # Si la profundidad almacenada es suficiente
            if stored_value['depth'] >= depth:
                if stored_value['flag'] == "EXACT":
                    return {"eval": stored_value['eval'], "best_move": stored_value['best_move'], "n_nodes": 0}
                elif stored_value['flag'] == "lower":
                    alpha = max(alpha, stored_value['eval'])
                elif stored_value['flag'] == "upper":
                    beta = min(beta, stored_value['eval'])

                if alpha >= beta and not stored_value['best_move'].null:
                    return {"eval": stored_value['eval'], "best_move": stored_value['best_move'], "n_nodes": 0}

        if depth == 0:
            n_nodes = n_nodes + 1
            evaluation = self.quiesence_search(search_board, alpha, beta)
            #evaluation = self.position_eval(search_board) if search_board.turn == "w" \
            #    else -self.position_eval(search_board)
            return {"eval": evaluation, "best_move": None, "n_nodes": n_nodes}

        if depth < self.R + 2:
            add_null_move = False

        moves = self.get_ordered_moves(search_board, add_null_move)

        best_value = -inf
        best_move = None

        for move in moves:
            search_board.move(move)
            self.update_hash_after_move(search_board)

            if move.null and add_null_move:
                alpha_beta_tree = self.alpha_beta_pruning_nm(search_board, depth - 1 - self.R,
                                                             -beta, -alpha, add_null_move = False)
            else:
                alpha_beta_tree = self.alpha_beta_pruning_nm(search_board, depth - 1, -beta, -alpha)

            self.update_hash_after_move(search_board)
            search_board.undo_move()

            value = -alpha_beta_tree["eval"]
            n_nodes = n_nodes + alpha_beta_tree["n_nodes"]

            #Se encuentra una jugada mejor de la que teníamos
            if best_value < value:
                best_value = value
                alpha = max(alpha, value)

                if not move.null:
                    best_move = move

            #Jugada demasiado buena. El oponente evitará esta variante porque es demasiado mala para el
            #En la tabla de transposiciones, es una cota inferior. Podría ser que encontraramos una jugada mejor aún
            if beta <= value:
                self.transpositions_table[iteration_hash] = {"eval": value, "best_move": move,
                                                             "depth": depth, "flag": "lower"}
                break

        #Vemos si hemos encontrado una jugada que superaba lo que teníamos o no, para la tabla de transposiciones
        if best_value <= alpha:
            flag = "upper"
        else:
            flag = "exact"

        self.transpositions_table[iteration_hash] = {"eval": best_value, "best_move": best_move,
                                                     "depth": depth, "flag": flag}

        return {"best_move": best_move, "eval": best_value, "n_nodes": n_nodes}


    def quiesence_search(self, search_board, alpha, beta):
        if search_board.checkmate:
            evaluation = 10000 if search_board.turn == "b" else -10000
            return evaluation

        lower_bound = self.position_eval(search_board)
        lower_bound = -lower_bound if search_board.turn == "b" else lower_bound

        if lower_bound >= beta:
            return beta

        if lower_bound > alpha:
            alpha = lower_bound

        captures = search_board.get_captures()
        captures = self.order_captures(search_board, captures)

        if not captures:
            return lower_bound

        for capture in captures:
            search_board.move(capture)
            value = -self.quiesence_search(search_board, -beta, -alpha)
            search_board.undo_move()

            if alpha < value:
                alpha = value

            if value >= beta:
                return value

        return alpha


    def check_null_move_conditions(self, test_board):
        if test_board.turn == "w":
            if test_board.w_check_state[0] > 0:
                return False
        else:
            if test_board.b_check_state[0] > 0:
                return False

        return True

    #Esta por ver, de momento esto no esta
    def iterative_deepening(self, test_board, depth):
        start_time = time.time()

        for iter_depth in range(1, depth + 1):
            self.itering = True
            time.sleep(0.25)

            if time.time() - start_time > self.max_time:
                break

            search = self.alpha_beta_pruning_nm(test_board, iter_depth)
            self.best_move = search["best_move"]
            self.eval = search["eval"] if test_board.turn == "w" else -search["eval"]
            print(self.best_move, self.eval)

        self.itering = False

    def init_hash_table(self):
        #board
        Z_table = []
        board_hash = [[[random.randint(0, pow(2,64)) for piece in range(12)] for row in range(8)] for col in range(8)]
        Z_table.append(board_hash)

        #turn
        Z_table.append(random.randint(0,pow(2,64)))

        #en passant
        en_passant_rows = [[random.randint(0, pow(2,64)) for col in range(cts.board_cols)] for p_row in range(2)]
        Z_table.append(en_passant_rows)

        #castling_rights
        castle_rights = [random.randint(0, pow(2,64)) for castle_right in range(4)]
        Z_table.append(castle_rights)

        self.z_table = Z_table

    def hash_position(self, test_board):
        z_hash = 0
        for row in range(cts.board_rows):
            for col in range(cts.board_cols):
                if not test_board.squares[row][col].isempty():
                    piece = test_board.squares[row][col].piece
                    piece_square_hash = cts.hash_indexes[piece.type][piece.color]
                    z_hash ^= self.z_table[0][row][col][piece_square_hash]

        if test_board.turn == "b":
            z_hash ^= self.z_table[1]

        if test_board.en_passant_pos is not None:
            if test_board.en_passant_pos[0] == 3:
                z_hash ^= self.z_table[2][0][test_board.en_passant_pos[1]]
            else:
                z_hash ^= self.z_table[2][1][test_board.en_passant_pos[1]]

        for right in test_board.castling_rights:
            z_hash ^= self.z_table[3][cts.hash_indexes[right]]

        self.z_hash = z_hash

    def update_hash_after_move(self, test_board):
        if test_board.move_history[-1][0].null:
            self.z_hash ^= self.z_table[1]
            return

        (move, piece, captured_piece, (en_passant_pos, en_passant_target_pos),
         (castling_rights, has_moved, castling_move), move_state) = test_board.move_history[-1]

        self.z_hash ^= self.z_table[0][move.initial_pos[0]][move.initial_pos[1]][cts.hash_indexes[piece.type][piece.color]]
        self.z_hash ^= self.z_table[0][move.landing_pos[0]][move.landing_pos[1]][cts.hash_indexes[piece.type][piece.color]]

        if move.is_passant:
            self.z_hash ^= (
                self.z_table)[0][en_passant_pos[0]][en_passant_pos[1]][cts.hash_indexes["pawn"][piece.opp_color]]
        elif captured_piece is not None:
            self.z_hash ^= (
                self.z_table)[0][move.landing_pos[0]][move.landing_pos[1]][cts.hash_indexes[captured_piece.type][captured_piece.color]]

        self.z_hash ^= self.z_table[1]

        if en_passant_pos is not None:
            if en_passant_pos[0] == 3:
                self.z_hash ^= self.z_table[2][0][en_passant_pos[1]]
            else:
                self.z_hash ^= self.z_table[2][1][en_passant_pos[1]]

        if test_board.en_passant_pos is not None:
            if test_board.en_passant_pos[0] == 3:
                self.z_hash ^= self.z_table[2][0][test_board.en_passant_pos[1]]
            else:
                self.z_hash ^= self.z_table[2][1][test_board.en_passant_pos[1]]

        if castling_rights != test_board.castling_rights:
            for right in castling_rights:
                if right not in test_board.castling_rights:
                    self.z_hash ^= self.z_table[3][cts.hash_indexes[right]]

    def get_best_move(self, test_board, depth):
        self.best_move = None
        self.iterative_deepening(test_board, depth)
        self.add_null_move = True

        return self.best_move, self.eval


