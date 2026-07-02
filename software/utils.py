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

def _findKingPos(board, kingColor):
    from pieces import King
    for x in range(8):
        for y in range(8):
            p = board[x][y]
            if p is not None and isinstance(p, King) and p.color == kingColor:
                return (x, y)
    return None


def generateLegalMoves(piece):
    """
    Returns a filtered move list for `piece` such that none of the moves
    leave that side's king in check. This automatically prevents pinned pieces
    from moving illegally.
    """
    from pieces import King
    from utils import isKingInCheck  # safe even within same module in your setup

    # Pseudo-legal moves from the piece's own movement rules
    pseudo = piece.generateMoveList() or []
    if not pseudo:
        piece.moveList = []
        return []

    board = piece.board
    color = piece.color

    legal = []
    from_x, from_y = piece.position

    for (to_x, to_y) in list(pseudo):
        captured = board[to_x][to_y]

        # --- simulate ---
        board[from_x][from_y] = None
        board[to_x][to_y] = piece
        old_pos = piece.position
        piece.position = (to_x, to_y)

        in_check, _ = isKingInCheck(board, color)

        # --- undo ---
        piece.position = old_pos
        board[from_x][from_y] = piece
        board[to_x][to_y] = captured

        if not in_check:
            legal.append((to_x, to_y))

    piece.moveList = legal
    return legal



def board_to_fen(board, turn):
    """
    Build a FEN string from your board.
    Assumptions:
      - No castling rights implemented => "-"
      - No en-passant => "-"
      - Halfmove/fullmove not tracked => "0 1"
    Your board coords: board[x][y] with y=0 as White back rank.
    FEN ranks go from 8 -> 1, so we iterate y=7 down to 0.
    """
    piece_map = {
        "Pawn": "p",
        "Rook": "r",
        "Knight": "n",
        "Bishop": "b",
        "Queen": "q",
        "King": "k",
    }

    ranks = []
    for y in range(7, -1, -1):
        empty = 0
        rank = ""
        for x in range(8):
            p = board[x][y]
            if p is None:
                empty += 1
            else:
                if empty:
                    rank += str(empty)
                    empty = 0
                name = type(p).__name__
                ch = piece_map.get(name, "?")
                if ch == "?":
                    raise ValueError(f"Unknown piece type for FEN: {name}")
                if p.color == "white":
                    ch = ch.upper()
                rank += ch
        if empty:
            rank += str(empty)
        ranks.append(rank)

    placement = "/".join(ranks)
    side = "w" if turn == 0 else "b"
    castling = "-"
    ep = "-"
    halfmove = "0"
    fullmove = "1"
    return f"{placement} {side} {castling} {ep} {halfmove} {fullmove}"


def _uci_write(proc, cmd):
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()


def get_stockfish_top_moves(fen, stockfish_path, depth=15, multipv=3, timeout_sec=2.5):
    import subprocess
    import time
    """
    Returns a list of up to `multipv` best moves as UCI strings (e.g. 'e2e4'),
    ordered best->worse according to Stockfish.
    Requires a Stockfish binary at stockfish_path.
    """
    proc = subprocess.Popen(
        [stockfish_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        # Handshake
        _uci_write(proc, "uci")
        # Wait for uciok
        start = time.time()
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if "uciok" in line:
                break
            if time.time() - start > timeout_sec:
                break

        _uci_write(proc, f"setoption name MultiPV value {multipv}")
        _uci_write(proc, "isready")
        # Wait for readyok
        start = time.time()
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if "readyok" in line:
                break
            if time.time() - start > timeout_sec:
                break

        _uci_write(proc, f"position fen {fen}")
        _uci_write(proc, f"go depth {depth}")

        # Parse info multipv lines: "info multipv N ... pv <move1> <move2> ..."
        top = {}  # multipv_index -> first move
        bestmove = None

        start = time.time()
        while True:
            line = proc.stdout.readline()
            if not line:
                break

            line = line.strip()

            if line.startswith("info ") and " multipv " in line and " pv " in line:
                # Example: info depth 15 ... multipv 2 ... pv e2e4 e7e5 ...
                parts = line.split()
                try:
                    mp_idx = parts.index("multipv")
                    pv_idx = parts.index("pv")
                    n = int(parts[mp_idx + 1])
                    first_move = parts[pv_idx + 1] if pv_idx + 1 < len(parts) else None
                    if first_move:
                        top[n] = first_move
                except Exception:
                    pass

            if line.startswith("bestmove "):
                parts = line.split()
                bestmove = parts[1] if len(parts) > 1 else None
                break

            if time.time() - start > timeout_sec:
                break

        # Build ordered list 1..multipv, fall back to bestmove if needed
        moves = [top.get(i) for i in range(1, multipv + 1)]
        moves = [m for m in moves if m]

        if not moves and bestmove and bestmove != "(none)":
            moves = [bestmove]

        return moves[:multipv]

    finally:
        try:
            _uci_write(proc, "quit")
        except Exception:
            pass
        try:
            proc.kill()
        except Exception:
            pass


def uci_to_coords(uci):
    """
    Convert a UCI move like 'e2e4' to ((from_x,from_y),(to_x,to_y))
    using your coordinate system:
      x: a->0 ... h->7
      y: rank1->0 ... rank8->7
    """
    if not uci or len(uci) < 4:
        return None
    file_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    f1, r1, f2, r2 = uci[0], uci[1], uci[2], uci[3]
    if f1 not in file_map or f2 not in file_map:
        return None
    try:
        y1 = int(r1) - 1
        y2 = int(r2) - 1
    except ValueError:
        return None
    x1 = file_map[f1]
    x2 = file_map[f2]
    if not (0 <= y1 < 8 and 0 <= y2 < 8):
        return None
    return (x1, y1), (x2, y2)
