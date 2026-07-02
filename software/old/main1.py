import pygame
from sys import exit
import time

from pieces import Pawn, Rook, Knight, Bishop, Queen, King
from utils import (
    checkAllMovesColor, isKingInCheck, isCheckmate, generateLegalMoves,
    board_to_fen, get_stockfish_top_moves, uci_to_coords
)
#https://www.youtube.com/watch?v=AY9MnQ4x3zk


pygame.init()
width = 800
height = 800
select = None
curPiece = None
oldSelect = None
oldPiece = None
turn = 0  # 0 for white's turn, 1 for black

chessBoard = [[None for _ in range(8)] for _ in range(8)]

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Chess Game")
clock = pygame.time.Clock()


STOCKFISH_PATH = "stockfish/stockfish-macos-m1-apple-silicon"  # or "./stockfish" or "stockfish.exe" (set this correctly!)

hint_moves = []          # list of UCI strings like ["e2e4", "g1f3", ...]
hint_coords = []         # list of ((fx,fy),(tx,ty)) coords to highlight
hint_text = ""           # rendered text content
hint_font = pygame.font.SysFont(None, 30)



for i in range(8):
    chessBoard[i][1] = Pawn((i, 1), "white", chessBoard)
    chessBoard[i][6] = Pawn((i, 6), "black", chessBoard)
chessBoard[0][0] = Rook((0, 0), "white", chessBoard)
chessBoard[7][0] = Rook((7, 0), "white", chessBoard)
chessBoard[0][7] = Rook((0, 7), "black", chessBoard)
chessBoard[7][7] = Rook((7, 7), "black", chessBoard)
chessBoard[2][0] = Bishop((2, 0), "white", chessBoard)
chessBoard[5][0] = Bishop((5, 0), "white", chessBoard)
chessBoard[2][7] = Bishop((2, 7), "black", chessBoard)
chessBoard[5][7] = Bishop((5, 7), "black", chessBoard)
chessBoard[1][0] = Knight((1, 0), "white", chessBoard)
chessBoard[6][0] = Knight((6, 0), "white", chessBoard)
chessBoard[1][7] = Knight((1, 7), "black", chessBoard)
chessBoard[6][7] = Knight((6, 7), "black", chessBoard)
chessBoard[3][0] = King((3, 0), "white", chessBoard)
chessBoard[3][7] = King((3, 7), "black", chessBoard)
chessBoard[4][0] = Queen((4, 0), "white", chessBoard)
chessBoard[4][7] = Queen((4, 7), "black", chessBoard)

color = ["white", "black"]

# Draw chessboard background
background = [[pygame.Surface((width/8, height/8)) for _ in range(8)] for _ in range(8)]
for row in range(8):
    for col in range(8):
        color = (235, 235, 208) if (row + col) % 2 == 0 else (119, 148, 85)
        background[row][col].fill(color)
        screen.blit(background[row][col], (col * width / 8, row * height / 8))



while True:
    # Handle events - Close game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
            if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_h and (not game_over):
            fen = board_to_fen(chessBoard, turn)
            try:
                hint_moves = get_stockfish_top_moves(
                    fen,
                    STOCKFISH_PATH,
                    depth=15,
                    multipv=3
                )
            except Exception as e:
                hint_moves = []
                hint_text = f"Stockfish error: {e}"
                hint_coords = []
            else:
                if hint_moves:
                    hint_text = "Top moves: " + ", ".join(hint_moves)
                    hint_coords = []
                    for mv in hint_moves:
                        c = uci_to_coords(mv)
                        if c:
                            hint_coords.append(c)
                else:
                    hint_text = "No hint moves returned."
                    hint_coords = []


    # Draw chessboard and pieces
    for x in range(8):
        for y in range(8):
            screen.blit(background[y][x], (x * width / 8, y * height / 8))
            piece = chessBoard[x][y]
            if piece is not None:
                screen.blit(piece.surface, (x * width / 8 + piece.surface.get_width() / 2, y * height / 8 + piece.surface.get_height() / 2))

    # Handle mouse clicks for selecting and moving pieces
    if(pygame.mouse.get_pressed()[0]):
        pos = pygame.mouse.get_pos()
        oldSelect = select
        oldPiece = curPiece
        select = (pos[0] // (width // 8), pos[1] // (height // 8))
        curPiece = chessBoard[select[0]][select[1]]
        if curPiece is not None:
            if (turn == 0 and curPiece.color == "white") or (turn == 1 and curPiece.color == "black"):
                generateLegalMoves(curPiece)
            else:
                curPiece.moveList = []  # not your turn -> show nothing
        time.sleep(0.2)  # Simple debounce to avoid multiple selections
        
    print("1", select)
    print("1 color", curPiece.color if curPiece is not None else None)
    print("2", oldSelect)
    print("2 color", oldPiece.color if oldPiece is not None else None)
    
    if(oldPiece is not None): # check if last selected square had a piece
        generateLegalMoves(oldPiece)
        if(select in oldPiece.moveList): # check if new selected square is a valid move
            if(turn == 0 and oldPiece.color == "white" or turn == 1 and oldPiece.color == "black"): # check if it's the correct player's turn
                turn = 1 - turn # switch turns
                # Make the move

                chessBoard[oldSelect[0]][oldSelect[1]] = None
                oldPiece.move(select)
                chessBoard[select[0]][select[1]] = oldPiece
                # Reset selections
                curPiece, select, oldSelect, oldPiece = None, None, None, None


                # Check if white king is in check
                whiteInCheck, whiteCheckingPiece = isKingInCheck(chessBoard, "white")
                if whiteInCheck:
                    print("White King is in check!")
                    if isCheckmate(chessBoard, "white", whiteCheckingPiece):
                        print("WHITE IS IN CHECKMATE! Black wins!")
                    else:
                        print("White is in check but can escape")
                
                # Check if black king is in check
                blackInCheck, blackCheckingPiece = isKingInCheck(chessBoard, "black")
                if blackInCheck:
                    print("Black King is in check!")
                    if isCheckmate(chessBoard, "black", blackCheckingPiece):
                        print("BLACK IS IN CHECKMATE! White wins!")
                    else:
                        print("Black is in check but can escape")

                curPiece, select, oldSelect, oldPiece = None, None, None, None

            else:
                print("Not your turn!")
        else:
            # Reset selections if move is invalid
            curPiece = None
            select = None
            oldSelect = None
            oldPiece = None
        
    if(curPiece is not None):
        # show possible moves
        for i in curPiece.moveList:
            pygame.draw.rect(screen, (255, 0, 0), (i[0] * width / 8, i[1] * height / 8, width / 8, height / 8), 5)

    


    pygame.display.update()
    clock.tick(30)