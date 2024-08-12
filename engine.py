import pieces
import board
import constants as cts

def material_sum(eval_board):
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

def position_eval(eval_board):
    material_score = material_sum(eval_board)
    return material_score/100

test_board = board.Board(fen = "r1bq1rk1/p1pp1ppp/2p5/2b5/2B1R3/8/PPP2PPP/RNBQ2K1 b KQkq - 0 1")

print(position_eval(test_board))