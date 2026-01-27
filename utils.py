def checkAllMovesColor(board, color, excludeKing=False):
    """Get all possible moves for a color. If excludeKing=True, don't call generateMoveList on the king."""
    from pieces import King
    moveList = []
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is not None and piece.color == color:
                if excludeKing and isinstance(piece, King):
                    continue
                pieceMoves = piece.generateMoveList()
                if pieceMoves is not None:
                    for move in pieceMoves:
                        moveList.append(move)
    return moveList


def isKingInCheck(board, kingColor):
    """Return (inCheck: bool, checkingPiece or None)."""
    from pieces import King

    # Find the king position
    kingPos = None
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is not None and isinstance(piece, King) and piece.color == kingColor:
                kingPos = piece.position
                break
        if kingPos:
            break

    if kingPos is None:
        return False, None

    enemyColor = "black" if kingColor == "white" else "white"

    # Check attacks from enemy pieces (EXCLUDING enemy king to avoid recursion)
    enemyKing = None
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is None or piece.color != enemyColor:
                continue

            if isinstance(piece, King):
                enemyKing = piece
                continue

            piece.generateMoveList()
            if kingPos in piece.moveList:
                return True, piece

    # Enemy king attacks adjacent squares (no safety filtering needed)
    if enemyKing is not None:
        ex, ey = enemyKing.position
        kx, ky = kingPos
        if max(abs(ex - kx), abs(ey - ky)) == 1:
            return True, enemyKing

    return False, None


def isSquareSafeForKing(board, kingColor, targetSquare):
    """True if targetSquare is NOT attacked by the enemy."""
    from pieces import King

    enemyColor = "black" if kingColor == "white" else "white"
    tx, ty = targetSquare

    enemyKingPos = None

    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is None or piece.color != enemyColor:
                continue

            if isinstance(piece, King):
                enemyKingPos = piece.position
                continue

            piece.generateMoveList()
            if targetSquare in piece.moveList:
                return False

    # Enemy king adjacency attack
    if enemyKingPos is not None:
        ex, ey = enemyKingPos
        if max(abs(ex - tx), abs(ey - ty)) == 1:
            return False

    return True


def isCheckmate(board, kingColor, checkingPiece):
    """Check if the king is in checkmate"""
    from pieces import Rook, Bishop, Queen, King
    
    # Find the king
    kingPos = None
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is not None and isinstance(piece, King) and piece.color == kingColor:
                kingPos = piece.position
                break
        if kingPos:
            break
    
    if kingPos is None:
        return False
    
    # 3 ways to escape check:
    # 1. Move the king to a safe square
    kingPiece = board[kingPos[0]][kingPos[1]]
    kingMoves = kingPiece.generateMoveList()
    
    # If king has any safe moves, it's not checkmate
    if len(kingMoves) > 0:
        return False
    
    # 2. Capture the checking piece
    # Check if any ally piece can capture the checking piece
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is not None and piece.color == kingColor and not isinstance(piece, King):
                piece.generateMoveList()
                if checkingPiece.position in piece.moveList:
                    # Simulate the capture to make sure it doesn't leave king in check
                    original_piece = board[checkingPiece.position[0]][checkingPiece.position[1]]
                    board[checkingPiece.position[0]][checkingPiece.position[1]] = piece
                    board[i][j] = None
                    
                    inCheck, _ = isKingInCheck(board, kingColor)
                    
                    # Undo the move
                    board[i][j] = piece
                    board[checkingPiece.position[0]][checkingPiece.position[1]] = original_piece
                    
                    if not inCheck:
                        return False  # Can escape by capturing
    
    # 3. Block the check (only for sliding pieces: Rook, Bishop, Queen)
    if isinstance(checkingPiece, (Rook, Bishop, Queen)):
        checkingPath = []
        xDir = 1 if checkingPiece.position[0] > kingPos[0] else -1 if checkingPiece.position[0] < kingPos[0] else 0
        yDir = 1 if checkingPiece.position[1] > kingPos[1] else -1 if checkingPiece.position[1] < kingPos[1] else 0
        
        currX, currY = kingPos[0] + xDir, kingPos[1] + yDir
        while (currX, currY) != checkingPiece.position:
            checkingPath.append((currX, currY))
            currX += xDir
            currY += yDir
        
        # Check if any ally piece can block
        for blockPos in checkingPath:
            for i in range(8):
                for j in range(8):
                    piece = board[i][j]
                    if piece is not None and piece.color == kingColor and not isinstance(piece, King):
                        piece.generateMoveList()
                        if blockPos in piece.moveList:
                            # Simulate the block move to make sure it doesn't leave king in check
                            original_piece = board[blockPos[0]][blockPos[1]]
                            board[blockPos[0]][blockPos[1]] = piece
                            board[i][j] = None
                            
                            inCheck, _ = isKingInCheck(board, kingColor)
                            
                            # Undo the move
                            board[i][j] = piece
                            board[blockPos[0]][blockPos[1]] = original_piece
                            
                            if not inCheck:
                                return False  # Can escape by blocking
    
    return True  # It's checkmate