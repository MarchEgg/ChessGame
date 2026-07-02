import pygame
from sys import exit
import time

from pieces import Pawn, Rook, Knight, Bishop, Queen, King
from utils import (checkAllMovesColor, isKingInCheck, isCheckmate,
                   generateLegalMoves, board_to_fen, get_stockfish_top_moves,
                   uci_to_coords)
from hardware import Hardware

# ---------- Config ----------
SERIAL_PORT = "/dev/cu.usbmodem48CA432D585C2"   # <-- set this
USE_HARDWARE = True

# How long the board must be stable (no sensor changes) before we try to
# commit a move, in seconds. Prevents flicker / mid-motion false commits.
SETTLE_TIME = 0.35

# After this many seconds with no move, auto-show Stockfish's top moves.
IDLE_HINT_SECONDS = 10.0

# LED colors (0xRRGGBB)
COL_SELECTED   = 0x0040FF
COL_LEGAL      = 0x004000
COL_CAPTURE    = 0x400000
COL_CHECK      = 0xFF0000
COL_LAST_MOVE  = 0x403000
COL_HINT_FROM  = 0x000080
COL_HINT_TO    = 0x008080
COL_ERROR      = 0xFF00FF   # illegal / confused state
COL_TURN       = 0x080808   # dim white under every piece of the player to move

pygame.init()
width = 800
height = 800
select = None
curPiece = None
oldSelect = None
oldPiece = None
turn = 0

chessBoard = [[None for _ in range(8)] for _ in range(8)]

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Chess Game")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 72)
game_over = False
game_over_text = ""

mouse_was_down = False

STOCKFISH_PATH = "stockfish/stockfish-macos-m1-apple-silicon"

hint_moves = []
hint_coords = []
hint_text = ""
hint_font = pygame.font.SysFont(None, 30)

# ---------- Initial position ----------
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

background = [[pygame.Surface((width / 8, height / 8)) for _ in range(8)] for _ in range(8)]
for row in range(8):
    for col in range(8):
        bg_color = (235, 235, 208) if (row + col) % 2 == 0 else (119, 148, 85)
        background[row][col].fill(bg_color)
        screen.blit(background[row][col], (col * width / 8, row * height / 8))

hw = None
if USE_HARDWARE:
    try:
        hw = Hardware(SERIAL_PORT)
        print("Hardware connected.")
    except Exception as e:
        print(f"Hardware unavailable ({e}); running UI only.")
        hw = None

# ---------- Coordinate helpers ----------
def xy_to_square(x, y):
    return y * 8 + x

def square_to_xy(sq):
    return (sq % 8, sq // 8)

def current_occupancy_from_board():
    s = []
    for row in range(8):
        for col in range(8):
            s.append('1' if chessBoard[col][row] is not None else '0')
    return ''.join(s)

# ---------- Physical move detection ----------
last_committed_occ = current_occupancy_from_board()
last_seen_occ = last_committed_occ
last_change_time = time.time()
last_move = None
king_check_square = None
error_squares = set()
last_move_time = time.time()

def diff_occupancy(old, new):
    emptied = set()
    filled = set()
    for i in range(64):
        if old[i] == '1' and new[i] == '0':
            emptied.add(i)
        elif old[i] == '0' and new[i] == '1':
            filled.add(i)
    return emptied, filled

def try_detect_move(new_occ):
    """
    Given a settled sensor occupancy, identify which legal move was played.
    Returns ((fx,fy),(tx,ty)) or None. On ambiguity/illegality populates
    error_squares.
    """
    global error_squares
    error_squares = set()

    emptied, filled = diff_occupancy(last_committed_occ, new_occ)
    player = "white" if turn == 0 else "black"

    # --- Non-capture move: 1 emptied, 1 filled ---
    if len(emptied) == 1 and len(filled) == 1:
        from_sq = next(iter(emptied))
        to_sq = next(iter(filled))
        fx, fy = square_to_xy(from_sq)
        tx, ty = square_to_xy(to_sq)
        piece = chessBoard[fx][fy]
        if piece is None or piece.color != player:
            error_squares = emptied | filled
            return None
        legal = generateLegalMoves(piece) or []
        if (tx, ty) in legal:
            return (fx, fy), (tx, ty)
        error_squares = emptied | filled
        return None

    # --- Capture: 1 emptied, 0 filled ---
    # Attacker's source went 1->0. Victim's square was 1, still 1
    # (attacker is there now), so it doesn't appear in the diff.
    if len(emptied) == 1 and len(filled) == 0:
        from_sq = next(iter(emptied))
        fx, fy = square_to_xy(from_sq)
        piece = chessBoard[fx][fy]
        if piece is None or piece.color != player:
            error_squares = emptied
            return None
        legal = generateLegalMoves(piece) or []
        candidates = []
        for (tx, ty) in legal:
            target = chessBoard[tx][ty]
            if target is not None and target.color != player:
                if new_occ[xy_to_square(tx, ty)] == '1':
                    candidates.append((tx, ty))
        if len(candidates) == 1:
            tx, ty = candidates[0]
            return (fx, fy), (tx, ty)
        if len(candidates) > 1:
            error_squares = {from_sq} | {xy_to_square(x, y) for (x, y) in candidates}
            return None
        error_squares = emptied
        return None

    # --- Any other shape is mid-motion / illegal state ---
    error_squares = emptied | filled
    return None

def request_hints():
    """Ask Stockfish for top moves and populate hint state."""
    global hint_moves, hint_text, hint_coords
    fen = board_to_fen(chessBoard, turn)
    print("FEN:", fen)
    try:
        hint_moves = get_stockfish_top_moves(fen, STOCKFISH_PATH, depth=15, multipv=3)
    except Exception as e:
        hint_moves = []
        hint_text = f"Stockfish error: {e}"
        hint_coords = []
        return
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

def apply_move(frm, to):
    global turn, game_over, game_over_text, last_committed_occ, last_move
    global king_check_square, last_move_time

    fx, fy = frm
    tx, ty = to
    piece = chessBoard[fx][fy]
    if piece is None:
        return False

    chessBoard[fx][fy] = None
    chessBoard[tx][ty] = piece
    piece.position = (tx, ty)
    turn = 1 - turn
    last_move = (frm, to)
    last_move_time = time.time()

    king_check_square = None
    for color_to_check in ("white", "black"):
        inCheck, checker = isKingInCheck(chessBoard, color_to_check)
        if inCheck:
            for x in range(8):
                for y in range(8):
                    p = chessBoard[x][y]
                    if p is not None and isinstance(p, King) and p.color == color_to_check:
                        king_check_square = xy_to_square(x, y)
            if isCheckmate(chessBoard, color_to_check, checker):
                game_over = True
                winner = "Black" if color_to_check == "white" else "White"
                game_over_text = f"Checkmate! {winner} wins!"

    last_committed_occ = current_occupancy_from_board()
    return True

# ---------- LED rendering ----------
def update_leds():
    if hw is None:
        return
    hw.clear()

    current_player = "white" if turn == 0 else "black"

    # Dim highlight under every piece of the player whose turn it is.
    # Drawn first so stronger highlights below override it.
    for x in range(8):
        for y in range(8):
            p = chessBoard[x][y]
            if p is not None and p.color == current_player:
                hw.set_led(xy_to_square(x, y), COL_TURN)

    if last_move is not None:
        (fx, fy), (tx, ty) = last_move
        hw.set_led(xy_to_square(fx, fy), COL_LAST_MOVE)
        hw.set_led(xy_to_square(tx, ty), COL_LAST_MOVE)

    emptied, _ = diff_occupancy(last_committed_occ, last_seen_occ)
    own_lifted = []
    for sq in emptied:
        fx, fy = square_to_xy(sq)
        p = chessBoard[fx][fy]
        if p is not None and p.color == current_player:
            own_lifted.append((sq, p))

    if len(own_lifted) == 1:
        sq, piece = own_lifted[0]
        hw.set_led(sq, COL_SELECTED)
        legal = generateLegalMoves(piece) or []
        for (tx, ty) in legal:
            target_sq = xy_to_square(tx, ty)
            if chessBoard[tx][ty] is not None:
                hw.set_led(target_sq, COL_CAPTURE)
            else:
                hw.set_led(target_sq, COL_LEGAL)

    for (frm, to) in hint_coords:
        hw.set_led(xy_to_square(*frm), COL_HINT_FROM)
        hw.set_led(xy_to_square(*to), COL_HINT_TO)

    if king_check_square is not None:
        hw.set_led(king_check_square, COL_CHECK)

    for sq in error_squares:
        hw.set_led(sq, COL_ERROR)

    hw.show()

# ---------- Main loop ----------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if hw is not None:
                hw.close()
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h and (not game_over):
                request_hints()

    # ----- Physical board input with settling -----
    if hw is not None and not game_over:
        occ = hw.get_occupancy()
        now = time.time()

        if occ != last_seen_occ:
            last_seen_occ = occ
            last_change_time = now

        if occ != last_committed_occ and (now - last_change_time) > SETTLE_TIME:
            move = try_detect_move(occ)
            if move is not None:
                frm, to = move
                apply_move(frm, to)
                hint_coords = []
                hint_text = ""
                error_squares = set()

    # Auto-suggest after IDLE_HINT_SECONDS of no moves
    if (not game_over) and (not hint_coords) and \
       (time.time() - last_move_time) > IDLE_HINT_SECONDS:
        request_hints()
        # Reset so we don't refire continuously; next refresh after another move.
        last_move_time = time.time()

    # ----- Draw Pygame board -----
    for x in range(8):
        for y in range(8):
            screen.blit(background[y][x], (x * width / 8, y * height / 8))
            piece = chessBoard[x][y]
            if piece is not None:
                sq = width // 8
                px = x * sq + (sq - piece.surface.get_width()) // 2
                py = y * sq + (sq - piece.surface.get_height()) // 2
                screen.blit(piece.surface, (px, py))

    mouse_down = pygame.mouse.get_pressed()[0]
    if (not game_over) and mouse_down and (not mouse_was_down):
        pos = pygame.mouse.get_pos()
        oldSelect = select
        oldPiece = curPiece
        select = (pos[0] // (width // 8), pos[1] // (height // 8))
        curPiece = chessBoard[select[0]][select[1]]
        if curPiece is not None:
            if (turn == 0 and curPiece.color == "white") or (turn == 1 and curPiece.color == "black"):
                generateLegalMoves(curPiece)
            else:
                curPiece.moveList = []
    mouse_was_down = mouse_down

    if (not game_over and oldPiece is not None):
        generateLegalMoves(oldPiece)
        if select in oldPiece.moveList:
            if (turn == 0 and oldPiece.color == "white") or (turn == 1 and oldPiece.color == "black"):
                apply_move(oldSelect, select)
                curPiece, select, oldSelect, oldPiece = None, None, None, None
            else:
                curPiece, select, oldSelect, oldPiece = None, None, None, None
        else:
            curPiece, select, oldSelect, oldPiece = None, None, None, None

    if curPiece is not None:
        for i in curPiece.moveList:
            pygame.draw.rect(screen, (255, 0, 0),
                             (i[0] * width / 8, i[1] * height / 8, width / 8, height / 8), 5)

    if hint_coords and (not game_over):
        sq = width // 8
        for (frm, to) in hint_coords:
            fx, fy = frm
            tx, ty = to
            pygame.draw.rect(screen, (0, 0, 255), (fx * sq, fy * sq, sq, sq), 4)
            pygame.draw.rect(screen, (0, 255, 255), (tx * sq, ty * sq, sq, sq), 4)

    if hint_text:
        surf = hint_font.render(hint_text, True, (255, 255, 255))
        screen.blit(surf, (10, 10))

    if game_over:
        text_surf = font.render(game_over_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(width // 2, height // 2))
        pad = 20
        box_rect = pygame.Rect(text_rect.left - pad, text_rect.top - pad,
                               text_rect.width + 2 * pad, text_rect.height + 2 * pad)
        pygame.draw.rect(screen, (0, 0, 0), box_rect)
        screen.blit(text_surf, text_rect)

    update_leds()

    pygame.display.update()
    clock.tick(30)
