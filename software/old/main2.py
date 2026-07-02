import pygame
from sys import exit
import time

from pieces import Pawn, Rook, Knight, Bishop, Queen, King
from utils import (checkAllMovesColor, isKingInCheck, isCheckmate,
                   generateLegalMoves, board_to_fen, get_stockfish_top_moves,
                   uci_to_coords)
from hardware import Hardware

# ---------- Config ----------
SERIAL_PORT = "/dev/cu.usbmodem48CA432D585C2"  # <-- set this! Windows: "COM5", Linux: "/dev/ttyUSB0"
USE_HARDWARE = True                       # set False to run UI only

# LED colors (0xRRGGBB)
COL_SELECTED   = 0x0040FF   # lifted piece's source square
COL_LEGAL      = 0x004000   # legal destinations for lifted piece
COL_CAPTURE    = 0x400000   # legal captures
COL_CHECK      = 0xFF0000   # king in check
COL_LAST_MOVE  = 0x403000   # last move highlight
COL_HINT_FROM  = 0x000080
COL_HINT_TO    = 0x008080

pygame.init()
width = 800
height = 800
select = None
curPiece = None
oldSelect = None
oldPiece = None
turn = 0  # 0 for white, 1 for black

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

# ---------- Board background ----------
background = [[pygame.Surface((width / 8, height / 8)) for _ in range(8)] for _ in range(8)]
for row in range(8):
    for col in range(8):
        bg_color = (235, 235, 208) if (row + col) % 2 == 0 else (119, 148, 85)
        background[row][col].fill(bg_color)
        screen.blit(background[row][col], (col * width / 8, row * height / 8))

# ---------- Hardware ----------
hw = None
if USE_HARDWARE:
    try:
        hw = Hardware(SERIAL_PORT)
        print("Hardware connected.")
    except Exception as e:
        print(f"Hardware unavailable ({e}); running UI only.")
        hw = None

# ---------- Coordinate helpers ----------
# Physical board "square index" = row * 8 + col, where row 0 is top of
# screen (rank 8 for black's view) and col 0 is leftmost file.
#
# Your Pygame board uses (x, y) where x is file (0=left) and y is rank
# (0=white back rank, 7=black back rank). The Pygame render draws y=0
# at the TOP of the screen, so row = y and col = x (from screen POV).
# Expected initial occupancy: ranks 1,2,7,8 occupied.

def xy_to_square(x, y):
    """Pygame (x, y) -> physical square index 0-63."""
    return y * 8 + x

def square_to_xy(sq):
    return (sq % 8, sq // 8)

def current_occupancy_from_board():
    """Build a 64-char occupancy string matching what the hardware SHOULD see
    given the logical chessBoard state. Uses the same row*8+col indexing."""
    s = []
    for row in range(8):
        for col in range(8):
            s.append('1' if chessBoard[col][row] is not None else '0')
    return ''.join(s)

# ---------- Physical move detection ----------
# The board is "at rest" when its occupancy matches the logical board.
# A move starts when one or more pieces get lifted. The move commits when
# occupancy again matches some legal continuation of the game.

last_committed_occ = current_occupancy_from_board()
lifted_squares = set()   # squares (0-63) currently lifted from their home
last_move = None         # ((fx, fy), (tx, ty)) of last committed move
king_check_square = None # square index of checked king, if any

def diff_occupancy(old, new):
    """Return (emptied, filled) as sets of square indices."""
    emptied = set()
    filled = set()
    for i in range(64):
        if old[i] == '1' and new[i] == '0':
            emptied.add(i)
        elif old[i] == '0' and new[i] == '1':
            filled.add(i)
    return emptied, filled

def all_legal_moves_for(color):
    """Yield (piece, (fx, fy), (tx, ty)) for every legal move of `color`."""
    for x in range(8):
        for y in range(8):
            p = chessBoard[x][y]
            if p is None or p.color != color:
                continue
            moves = generateLegalMoves(p) or []
            for (tx, ty) in moves:
                yield p, (x, y), (tx, ty)

def try_commit_move(new_occ):
    """If the current occupancy corresponds to a completed legal move from
    last_committed_occ, apply it and return ((fx,fy),(tx,ty)). Else None."""
    emptied, filled = diff_occupancy(last_committed_occ, new_occ)
    player = "white" if turn == 0 else "black"

    # Case A: simple non-capture move -> exactly 1 emptied, 1 filled
    if len(emptied) == 1 and len(filled) == 1:
        from_sq = next(iter(emptied))
        to_sq = next(iter(filled))
        fx, fy = square_to_xy(from_sq)
        tx, ty = square_to_xy(to_sq)
        piece = chessBoard[fx][fy]
        if piece is None or piece.color != player:
            return None
        legal = generateLegalMoves(piece) or []
        if (tx, ty) in legal:
            return (fx, fy), (tx, ty)

    # Case B: capture -> 2 emptied (attacker + victim), 1 filled (attacker's new square)
    # Note: victim's square started '1' and ends '1' (attacker there now), so
    # diff shows it as unchanged. We must match by searching legal captures.
    if len(emptied) == 2 and len(filled) == 1:
        to_sq = next(iter(filled))
        tx, ty = square_to_xy(to_sq)
        for from_sq in emptied:
            fx, fy = square_to_xy(from_sq)
            piece = chessBoard[fx][fy]
            if piece is None or piece.color != player:
                continue
            legal = generateLegalMoves(piece) or []
            if (tx, ty) in legal and chessBoard[tx][ty] is not None:
                # other emptied square should be the victim
                other = (emptied - {from_sq}).pop()
                if other == to_sq:
                    return (fx, fy), (tx, ty)

    # Case C: capture where victim was lifted, then attacker placed on victim's square.
    # Here occupancy diff has exactly 1 emptied (attacker's source) and 0 filled,
    # because victim's square '1' -> '0' (lifted) -> '1' (attacker placed) nets zero.
    # We only detect this after the motion fully settles, which matches Case B above
    # if victim is physically gone first. If the player removes victim AFTER placing
    # attacker, that's just Case A again (net: source emptied, victim square filled
    # by attacker and the old victim piece removed to side -> but the victim's square
    # stayed '1' throughout if attacker replaces instantly). Pragmatically Case A
    # and Case B cover what humans actually do.

    return None

def apply_move(frm, to):
    """Apply move on the logical board; returns True on success."""
    global turn, game_over, game_over_text, last_committed_occ, last_move
    global king_check_square

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

    king_check_square = None
    for color_to_check in ("white", "black"):
        inCheck, checker = isKingInCheck(chessBoard, color_to_check)
        if inCheck:
            # find king position
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

    # Last move highlight (dim, always visible)
    if last_move is not None:
        (fx, fy), (tx, ty) = last_move
        hw.set_led(xy_to_square(fx, fy), COL_LAST_MOVE)
        hw.set_led(xy_to_square(tx, ty), COL_LAST_MOVE)

    # If the player has lifted exactly one of their own pieces, show its legal moves
    current_player = "white" if turn == 0 else "black"
    if len(lifted_squares) == 1:
        sq = next(iter(lifted_squares))
        fx, fy = square_to_xy(sq)
        piece = chessBoard[fx][fy]
        if piece is not None and piece.color == current_player:
            hw.set_led(sq, COL_SELECTED)
            legal = generateLegalMoves(piece) or []
            for (tx, ty) in legal:
                target_sq = xy_to_square(tx, ty)
                if chessBoard[tx][ty] is not None:
                    hw.set_led(target_sq, COL_CAPTURE)
                else:
                    hw.set_led(target_sq, COL_LEGAL)

    # Hint highlights (Stockfish)
    for (frm, to) in hint_coords:
        hw.set_led(xy_to_square(*frm), COL_HINT_FROM)
        hw.set_led(xy_to_square(*to), COL_HINT_TO)

    # King in check
    if king_check_square is not None:
        hw.set_led(king_check_square, COL_CHECK)

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
                fen = board_to_fen(chessBoard, turn)
                print("FEN:", fen)
                try:
                    hint_moves = get_stockfish_top_moves(fen, STOCKFISH_PATH, depth=15, multipv=3)
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

    # ----- Physical board input -----
    if hw is not None and not game_over:
        occ = hw.get_occupancy()
        emptied, filled = diff_occupancy(last_committed_occ, occ)

        # Update set of currently-lifted squares for LED display
        lifted_squares = emptied.copy()

        # Try to commit a move whenever the occupancy changes
        if occ != last_committed_occ:
            move = try_commit_move(occ)
            if move is not None:
                frm, to = move
                apply_move(frm, to)
                lifted_squares.clear()
                # clear hints after a move
                hint_coords = []
                hint_text = ""

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

    # ----- Mouse input (still works alongside hardware) -----
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

    # Push LED state after all logic this frame
    update_leds()

    pygame.display.update()
    clock.tick(30)
