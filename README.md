# Smart Chess Board

A physical chessboard that plays alongside a desktop chess app. Hall-effect
sensors under each square detect where the pieces are, addressable LEDs light up
legal moves / checks / engine hints, and a [Stockfish](https://stockfishchess.org/)
integration suggests the best moves. The board talks to a Python + Pygame
program over a simple serial protocol.

## Demo

<!--
  ADD YOUR VIDEO HERE.

  Easiest option (GitHub): open this README in the GitHub web editor (or a PR/
  issue), then drag-and-drop your video file (.mp4/.mov, < 100 MB) into the text
  area. GitHub uploads it and pastes a URL like:

      https://github.com/user-attachments/assets/xxxxxxxx-....mp4

  Paste that URL on its own line below (replacing the placeholder) and GitHub
  renders an inline player.

  Alternatives:
    - Upload to YouTube and use a thumbnail link:
        [![Demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://youtu.be/VIDEO_ID)
    - Commit the file to the repo (only if small) and reference it:
        https://raw.githubusercontent.com/MarchEgg/ChessGame/main/docs/demo.mp4
-->

>  **Demo videocan you commit and push with -m"added readme"** 

## Project layout

```
.
├── software/          # Desktop app (Python + Pygame)
│   ├── main.py        # Game loop, UI, hardware sync, Stockfish hints
│   ├── pieces.py      # Piece classes + move generation
│   ├── utils.py       # Check/checkmate, legal moves, FEN, Stockfish helpers
│   ├── hardware.py    # Serial bridge to the board (occupancy in, LEDs out)
│   ├── images_png/    # Piece sprites
│   ├── stockfish/     # Stockfish engine (git-ignored — download separately)
│   └── old/           # Earlier prototypes
└── firmware/          # Arduino sketch (PlatformIO)
    └── src/main.cpp   # Sensor scanning + LED control
```

## Hardware

- **Controller:** Arduino Nano ESP32 (`arduino_nano_esp32`)
- **Sensors:** 64 hall-effect sensors read through four MCP23017 I²C GPIO
  expanders (addresses `0x23`, `0x25`, `0x26`, `0x27`)
- **Lighting:** WS2812B addressable LED strip (166 LEDs) driven by FastLED on
  pin 5
- Square-to-sensor and square-to-LED mappings live in `sensorMatrix` /
  `ledMatrix` in `firmware/src/main.cpp` — adjust these to match your wiring.

### Serial protocol

The firmware and `software/hardware.py` speak a simple line protocol at
**115200 baud**:

| Direction        | Message                | Meaning                                   |
|------------------|------------------------|-------------------------------------------|
| Arduino → Python | `READY`                | Board booted                              |
| Arduino → Python | `OCC <64 chars>`       | Occupancy: `1` = piece present, `0` = empty |
| Python → Arduino | `CLEAR`                | Turn all LEDs off                         |
| Python → Arduino | `FILL RRGGBB`          | Set all LEDs to one color                 |
| Python → Arduino | `LED <0-63> RRGGBB`    | Set one square's LED                      |
| Python → Arduino | `SHOW`                 | Flush LED changes                         |

Square index is `row * 8 + col`, matching the Pygame board.

## Software setup

Requires Python 3.

```bash
cd software
pip install pygame pyserial
```

### Stockfish (required for move hints)

The Stockfish engine is **not** committed (the binary is ~109 MB, over GitHub's
limit). Download it from <https://stockfishchess.org/download/> and place the
binary at the path referenced in `software/main.py`:

```python
STOCKFISH_PATH = "stockfish/stockfish-macos-m1-apple-silicon"
```

Update `STOCKFISH_PATH` to match your platform's binary name.

### Configure the serial port

In `software/main.py`, set the port your board enumerates as (or run without
hardware):

```python
SERIAL_PORT  = "/dev/cu.usbmodem48CA432D585C2"  # <-- your board's port
USE_HARDWARE = True                             # set False to run UI-only
```

### Run

```bash
cd software
python main.py
```

> Run from inside `software/`, since `STOCKFISH_PATH` and the image paths are
> resolved relative to that directory.

## Controls

- **Click** a piece to select it, then **click** a destination to move. Legal
  moves are highlighted.
- **`H`** — ask Stockfish for its top moves; suggestions are shown on screen and
  lit on the board.
- Hints also appear automatically after ~10 seconds of no moves
  (`IDLE_HINT_SECONDS`).
- On the physical board, lift and place pieces — the sensors detect the move
  once the position settles (`SETTLE_TIME`).

## Firmware setup

Built with [PlatformIO](https://platformio.org/).

```bash
cd firmware
pio run                # build
pio run --target upload # flash to the Nano ESP32
```

Dependencies (FastLED) are declared in `platformio.ini` and installed
automatically.
