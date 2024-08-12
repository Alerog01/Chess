class Move:
    def __init__(self, initial_pos, landing_pos, is_passant=False, promotion = ""):
        self.initial_pos = initial_pos
        self.landing_pos = landing_pos
        self.is_passant = is_passant
        self.promotion = promotion

    @staticmethod
    def list_to_squares(list_moves):
        att_squares = []
        for i in range(len(list_moves)):
            att_squares.append(list_moves[i].landing_pos)

        return att_squares
