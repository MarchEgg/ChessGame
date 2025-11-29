import pygame
from sys import exit
import time

from pieces import Pawn, Rook, Knight, Bishop, Queen

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
chessBoard[3][0] = Queen((3, 0), "white", chessBoard)
chessBoard[3][7] = Queen((3, 7), "black", chessBoard)


background = [[pygame.Surface((width/8, height/8)) for _ in range(8)] for _ in range(8)]
for row in range(8):
    for col in range(8):
        color = (235, 235, 208) if (row + col) % 2 == 0 else (119, 148, 85)
        background[row][col].fill(color)
        screen.blit(background[row][col], (col * width / 8, row * height / 8))



while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    for x in range(8):
        for y in range(8):
            screen.blit(background[y][x], (x * width / 8, y * height / 8))
            piece = chessBoard[x][y]
            if piece is not None:
                piece.generateMoveList()
                screen.blit(piece.surface, (x * width / 8 + piece.surface.get_width() / 2, y * height / 8 + piece.surface.get_height() / 2))

    if(pygame.mouse.get_pressed()[0]):
        pos = pygame.mouse.get_pos()
        oldSelect = select
        oldPiece = curPiece
        select = (pos[0] // (width // 8), pos[1] // (height // 8))
        curPiece = chessBoard[select[0]][select[1]]
        time.sleep(0.2)  # Simple debounce to avoid multiple selections
        
    print("1", select)
    print("1 color", curPiece.color if curPiece is not None else None)
    print("2", oldSelect)
    print("2 color", oldPiece.color if oldPiece is not None else None)
    
    if(oldPiece is not None):
        if(select in oldPiece.moveList):
            if(turn == 0 and oldPiece.color == "white" or turn == 1 and oldPiece.color == "black"):
                turn = 1 - turn
                chessBoard[oldSelect[0]][oldSelect[1]] = None
                oldPiece.move(select)
                chessBoard[select[0]][select[1]] = oldPiece
                curPiece = None
                select = None
                oldSelect = None
                oldPiece = None
            else:
                print("Not your turn!")
        else:
            curPiece = None
            select = None
            oldSelect = None
            oldPiece = None
        
    if(curPiece is not None):
        for i in curPiece.moveList:
            pygame.draw.rect(screen, (255, 0, 0), (i[0] * width / 8, i[1] * height / 8, width / 8, height / 8), 5)


    pygame.display.update()
    clock.tick(30)