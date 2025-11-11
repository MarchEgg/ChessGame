import pygame

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
        
chessBoard = [[None for _ in range(8)] for _ in range(8)]

for i in range(8):
    chessBoard[1][i] = Pawn((i, 1), "white")
    chessBoard[6][i] = Pawn((i, 6), "black")

pygame.init()
screen = pygame.display.set_mode((800, 400))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    
    pygame.display.update()