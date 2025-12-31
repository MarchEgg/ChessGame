import pygame

class ChessPiece:
    imageFilePath = ""
    position = (0, 0)
    color = ""
    moveList = []


class Pawn(ChessPiece):
    imageFilePath = "images/pawn.png"
    

    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((0, 100, 0))  # Placeholder for pawn image
    
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position
        direction = 1 if self.color == "white" else -1

        if self.board[x][y + direction] is None:
            self.moveList.append((x, y + direction))

        if (self.color == "white" and y == 1) or (self.color == "black" and y == 6):
            self.moveList.append((x, y + 2 * direction))
        
        try:
            if self.board[x - 1][y + direction] is not None:
                self.moveList.append((x - 1, y + direction))
        except IndexError:
            pass
        try: 
            if self.board[x + 1][y + direction] is not None:
                self.moveList.append((x + 1, y + direction))
        except IndexError:
            pass
        
        ml = self.moveList.copy()
        for i in ml:
            if self.board[i[0]][i[1]] is not None:
                if self.board[i[0]][i[1]].color == self.color:
                    self.moveList.remove(i)
        

    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Pawn")
        


class Rook(ChessPiece):
    imageFilePath = "images/rook.png"
    
    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((100, 0, 0))  # Placeholder for rook image
    
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position

        for i in range(x, 8):
            if i != x:
                self.moveList.append((i, y))
                if self.board[i][y] is not None:
                    break
        for i in range(x, -1, -1):
            if i != x:
                self.moveList.append((i, y))
                if self.board[i][y] is not None:
                    break
        for i in range(y, 8):
            if i != y:
                self.moveList.append((x, i))
                if self.board[x][i] is not None:
                    break
        for i in range(y, -1, -1):
            if i != y:
                self.moveList.append((x, i))
                if self.board[x][i] is not None:
                   break

        ml = self.moveList.copy()
        for i in ml:
            if self.board[i[0]][i[1]] is not None:
                if self.board[i[0]][i[1]].color == self.color:
                    self.moveList.remove(i)

    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Rook")
        

class Bishop(ChessPiece):
    imageFilePath = "images/bishop.png"
    # Implementation similar to Pawn and Rook
    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((0, 0, 100))  # Placeholder for bishop image
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position

        # Diagonal moves
        for i in range(1, 8):
            if x + i < 8 and y + i < 8:
                self.moveList.append((x + i, y + i))
                if self.board[x + i][y + i] is not None:
                    break
        for i in range(1, 8):
            if x - i >= 0 and y + i < 8:
                self.moveList.append((x - i, y + i))
                if self.board[x - i][y + i] is not None:
                    break
        for i in range(1, 8):
            if x + i < 8 and y - i >= 0:
                self.moveList.append((x + i, y - i))
                if self.board[x + i][y - i] is not None:
                    break
        for i in range(1, 8):
            if x - i >= 0 and y - i >= 0:
                self.moveList.append((x - i, y - i))
                if self.board[x - i][y - i] is not None:
                    break

        ml = self.moveList.copy()
        for i in ml:
            if self.board[i[0]][i[1]] is not None:
                if self.board[i[0]][i[1]].color == self.color:
                    self.moveList.remove(i)
                
    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Bishop")
        
class Knight(ChessPiece):
    imageFilePath = "images/knight.png"
    # Implementation similar to Pawn and Rook
    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((100, 100, 0))  # Placeholder for knight image

    def generateMoveList(self):
        self.moveList = []
        x, y = self.position

        # L-shaped moves
        potential_moves = [
            (x + 2, y + 1), (x + 2, y - 1),
            (x - 2, y + 1), (x - 2, y - 1),
            (x + 1, y + 2), (x + 1, y - 2),
            (x - 1, y + 2), (x - 1, y - 2)
        ]
        for move in potential_moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                if self.board[move[0]][move[1]] is None or self.board[move[0]][move[1]].color != self.color:
                    self.moveList.append(move)
        return self.moveList


    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Knight")

class Queen(ChessPiece):
    imageFilePath = "images/queen.png"
    
    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((0, 100, 100))  # Placeholder for queen image
    
    def generateMoveList(self):
        self.moveList = []
        # Combine Rook and Bishop move generation
        rook_like = Rook(self.position, self.color, self.board)
        rook_like.generateMoveList()
        bishop_like = Bishop(self.position, self.color, self.board)
        bishop_like.generateMoveList()
        self.moveList = rook_like.moveList + bishop_like.moveList
        return self.moveList

    
    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for Queen")

class King(ChessPiece):
    imageFilePath = "images/king.png"
    # Implementation similar to Pawn and Rook
    def __init__(self, position, color, board):
        self.position = position
        self.color = color
        self.board = board
        self.generateMoveList()
        self.surface = pygame.Surface((50, 50))
        self.surface.fill((150, 75, 0))  # Placeholder for king image

    def generateMoveList(self):
        self.moveList = []
        x, y = self.position

        # One square in any direction
        potential_moves = [
            (x + 1, y), (x - 1, y),
            (x, y + 1), (x, y - 1),
            (x + 1, y + 1), (x + 1, y - 1),
        ]
        for move in potential_moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                if self.board[move[0]][move[1]] is None or self.board[move[0]][move[1]].color != self.color:
                    self.moveList.append(move)

        return self.moveList
        
    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for King")
        
    
