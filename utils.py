def checkAllMovesColor(board, color):
    moveList = []
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece is not None and piece.color == color:
                pieceMoves = piece.generateMoveList()
                for move in pieceMoves:
                    moveList.append(move)
    return moveList