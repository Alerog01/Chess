import constants as cts
class Move:
    def __init__(self, initial_pos, landing_pos, is_passant=False, promotion="", null_move=False):
        self.initial_pos = initial_pos
        self.landing_pos = landing_pos
        self.is_passant = is_passant
        self.promotion = promotion
        self.null = null_move

    def is_capture(self, board):
        if not self.is_passant:
            if not board.squares[self.landing_pos[0]][self.landing_pos[1]].isempty():
                return True
        else:
            True

    @staticmethod
    def list_to_squares(list_moves):
        att_squares = []
        for i in range(len(list_moves)):
            att_squares.append(list_moves[i].landing_pos)

        return att_squares

    def __eq__(self, other):
        if isinstance(other, Move):
            return (self.initial_pos == other.initial_pos and self.landing_pos == other.landing_pos and
                    self.is_passant == other.is_passant and self.promotion == other.promotion)
        return False

    def __str__(self):
        return str(self.initial_pos) + str(self.landing_pos)