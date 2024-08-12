import constants as cts
import copy

class Square:
    def __init__(self, row, column):
        self.row = row
        self.column = column
        self.piece = None

    def add_piece(self, piece):
        self.piece = piece

    def remove_piece(self):
        self.piece = None

    def in_range(*args):
        for arg in args:
            if arg not in range(cts.board_rows):
                return False

        return True

    def isempty(self):
        if self.piece is None:
            return True

    def __str__(self):
        if self.piece is None:
            piece_str = ("ninguna")
        else:
            piece_str = self.piece
        return "Fila y columna: [{} {}]. Pieza: {}".format(self.row, self.column, piece_str)

    def __eq__(self, other):
        if self.isempty() != other.isempty():
            return False
        if (self.piece == other.piece and
                self.row == other.row and
                self.column == other.column):
            return True
        else:
            return False
