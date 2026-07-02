"""
Hardware bridge to the physical chessboard.

Speaks a simple line protocol over serial with the Arduino firmware:
    Arduino -> Python:
        READY
        OCC <64-char string>   # '1' piece present, '0' empty
    Python -> Arduino:
        CLEAR
        FILL RRGGBB
        LED <square_index> RRGGBB
        SHOW
        PING

Square indexing matches the firmware: square = row * 8 + col,
using the same row/col as your Pygame board. Translate as needed.
"""

import threading
import time

try:
    import serial  # pyserial
except ImportError:
    serial = None


class Hardware:
    def __init__(self, port, baud=115200):
        if serial is None:
            raise RuntimeError("pyserial not installed. Run: pip install pyserial")
        self.ser = serial.Serial(port, baud, timeout=0.05)
        self._occ = "0" * 64          # latest occupancy from the board
        self._occ_lock = threading.Lock()
        self._stop = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        # give the Arduino a moment to reset after opening the port
        time.sleep(2.0)
        self.clear()
        self.show()

    def close(self):
        self._stop = True
        try:
            self.ser.close()
        except Exception:
            pass

    # --- reading ---
    def _read_loop(self):
        buf = ""
        while not self._stop:
            try:
                data = self.ser.read(128).decode(errors="ignore")
            except Exception:
                break
            if not data:
                continue
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                self._handle_line(line.strip())

    def _handle_line(self, line):
        if line.startswith("OCC "):
            bits = line[4:]
            if len(bits) == 64:
                with self._occ_lock:
                    self._occ = bits

    def get_occupancy(self):
        """Return the 64-char occupancy string as seen by the sensors."""
        with self._occ_lock:
            return self._occ

    # --- writing ---
    def _send(self, cmd):
        try:
            self.ser.write((cmd + "\n").encode())
        except Exception:
            pass

    def clear(self):
        self._send("CLEAR")

    def fill(self, rgb):
        self._send(f"FILL {rgb:06X}")

    def set_led(self, square, rgb):
        """square is 0-63 using row*8+col (same convention as the firmware)."""
        self._send(f"LED {square} {rgb:06X}")

    def show(self):
        self._send("SHOW")
