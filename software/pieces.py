import pygame
import os

# Cache loaded piece surfaces so we only rasterize each SVG once
_IMAGE_CACHE = {}

def load_piece_surface(piece_name: str, color: str, size: int = 80) -> pygame.Surface:
    suffix = "w" if color == "white" else "b"
    filename = f"{piece_name}-{suffix}.png"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, "images_png", filename)

    key = (path, size)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing piece image: {path}")

    surf = pygame.image.load(path).convert_alpha()
    surf = pygame.transform.smoothscale(surf, (size, size))

    _IMAGE_CACHE[key] = surf
    return surf





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
        self.surface = load_piece_surface("pawn", self.color, size=80)
    
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position
        direction = 1 if self.color == "white" else -1

        # Forward move (only if square is empty)
        ny = y + direction
        if 0 <= ny < 8 and self.board[x][ny] is None:
            self.moveList.append((x, ny))
            # double move
            ny2 = y + 2 * direction
            if ((self.color == "white" and y == 1) or (self.color == "black" and y == 6)) and 0 <= ny2 < 8:
                if self.board[x][ny2] is None:
                    self.moveList.append((x, ny2))
        
        # Diagonal captures (only if there's an enemy piece)
        try:
            if self.board[x - 1][y + direction] is not None and self.board[x - 1][y + direction].color != self.color:
                self.moveList.append((x - 1, y + direction))
        except IndexError:
            pass
        try: 
            if self.board[x + 1][y + direction] is not None and self.board[x + 1][y + direction].color != self.color:
                self.moveList.append((x + 1, y + direction))
        except IndexError:
            pass
        
        return self.moveList
        

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
        self.surface = load_piece_surface("rook", self.color, size=80)
    
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
        return self.moveList

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
        self.surface = load_piece_surface("bishop", self.color, size=80)
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
        return self.moveList
                
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
        self.surface = load_piece_surface("knight", self.color, size=80)

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
        self.surface = load_piece_surface("queen", self.color, size=80)
    
    def generateMoveList(self):
        self.moveList = []
        x, y = self.position

        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),    # rook-like
            (1, 1), (1, -1), (-1, 1), (-1, -1),  # bishop-like
        ]

        for dx, dy in directions:
            cx, cy = x + dx, y + dy
            while 0 <= cx < 8 and 0 <= cy < 8:
                target = self.board[cx][cy]
                if target is None:
                    self.moveList.append((cx, cy))
                else:
                    if target.color != self.color:
                        self.moveList.append((cx, cy))
                    break
                cx += dx
                cy += dy

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
        self.surface = load_piece_surface("king", self.color, size=80)

    def generateMoveList(self):
        from utils import isSquareSafeForKing
        
        self.moveList = []
        x, y = self.position

        # One square in any direction
        potential_moves = [
            (x + 1, y), (x - 1, y),
            (x, y + 1), (x, y - 1),
            (x + 1, y + 1), (x + 1, y - 1),
            (x - 1, y + 1), (x - 1, y - 1),
        ]
        for move in potential_moves:
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                if self.board[move[0]][move[1]] is None or self.board[move[0]][move[1]].color != self.color:
                    # Simulate the move to check if king would be in check
                    original_piece = self.board[move[0]][move[1]]
                    original_pos = self.position
                    
                    self.board[move[0]][move[1]] = self
                    self.board[x][y] = None
                    self.position = move
                    
                    # Check if this square is safe
                    isSafe = isSquareSafeForKing(self.board, self.color, move)
                    
                    # Undo the simulated move
                    self.position = original_pos
                    self.board[x][y] = self
                    self.board[move[0]][move[1]] = original_piece
                    
                    # Only add move if it doesn't put king in check
                    if isSafe:
                        self.moveList.append(move)

        return self.moveList
        
    def move(self, newPosition):
        if newPosition in self.moveList:
            self.position = newPosition
            self.generateMoveList()
        else:
            raise ValueError("Invalid move for King")
        
    
