import pygame
from sys import exit
import time


#https://www.youtube.com/watch?v=AY9MnQ4x3zk

class ChessPiece:
    imageFilePath = ""
    position = (0, 0)
    color = ""
    moveList = []


class Pawn(ChessPiece):
    imageFilePath = "images/pawn.png"
    

    def __init__(self, position, color):
        self.position = position
        self.color = color
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((0, 100, 0))  # Placeholder for pawn image
    
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position
        direction = 1 if self.color == "white" else -1

        self.moveList.append((x, y + direction))

        if (self.color == "white" and y == 1) or (self.color == "black" and y == 6):
            self.moveList.append((x, y + 2 * direction))

        self.moveList.append((x - 1, y + direction))
        self.moveList.append((x + 1, y + direction))
        
    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Pawn")


        








pygame.init()
width = 800
height = 800
select = None
curPiece = None
oldSelect = None
oldPiece = None

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Chess Game")
clock = pygame.time.Clock()



chessBoard = [[None for _ in range(8)] for _ in range(8)]

for i in range(8):
    chessBoard[1][i] = Pawn((i, 1), "white")
    chessBoard[6][i] = Pawn((i, 6), "black")





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

    for row in range(8):
        for col in range(8):
            screen.blit(background[row][col], (col * width / 8, row * height / 8))
            piece = chessBoard[row][col]
            if piece is not None:
                screen.blit(piece.surface, (col * width / 8 + piece.surface.get_width() / 2, row * height / 8 + piece.surface.get_height() / 2))
        
    if(pygame.mouse.get_pressed()[0]):
        pos = pygame.mouse.get_pos()
        oldSelect = select
        oldPiece = curPiece
        select = (pos[1] // (height // 8), pos[0] // (width // 8))
        curPiece = chessBoard[select[0]][select[1]]
        time.sleep(0.2)  # Simple debounce to avoid multiple selections
        
    print("1", select)
    print("2", oldSelect)
    
    if(oldPiece is not None):
        if((select[1], select[0]) in oldPiece.moveList):
            chessBoard[oldSelect[0]][oldSelect[1]] = None
            oldPiece.move((select[1], select[0]))
            chessBoard[select[0]][select[1]] = oldPiece
            curPiece = None
            select = None
            oldSelect = None
            oldPiece = None
        
    if(curPiece is not None):
        for i in curPiece.moveList:
            pygame.draw.rect(screen, (255, 0, 0), (i[0] * width / 8, i[1] * height / 8, width / 8, height / 8), 5)


    pygame.display.update()
    clock.tick(30)