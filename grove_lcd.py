"""
grove_lcd.py - CircuitPython driver for the Seeed Grove 16x2 LCD (I2C).

Works with the text controller at 0x3E and auto-detects the RGB backlight
chip (0x30 on v5.0 modules, 0x62 on older RGB modules). Monochrome modules
have no RGB chip, so set_backlight() quietly does nothing on those.

Usage:
    import board, busio
    from grove_lcd import GroveLCD

    i2c = busio.I2C(board.GP13, board.GP12)
    lcd = GroveLCD(i2c)
    lcd.set_backlight(0, 128, 255)
    lcd.message = "Hello\nWorld"
"""

import time

LCD_ADDR = 0x3E
_ROW_OFFSETS = (0x00, 0x40)


class GroveLCD:
    def __init__(self, i2c, cols=16, rows=2, lcd_addr=LCD_ADDR, rgb_addr="auto"):
        self.i2c = i2c
        self.cols = cols
        self.rows = rows
        self.lcd_addr = lcd_addr

        if rgb_addr == "auto":
            rgb_addr = self._detect_backlight()
        self.rgb_addr = rgb_addr  # 0x30, 0x62, or None

        self._init_display()

    # ---------- low level I2C ----------

    def _write(self, addr, data):
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(addr, bytes(data))
        finally:
            self.i2c.unlock()

    def _command(self, cmd):
        self._write(self.lcd_addr, [0x80, cmd])

    def _detect_backlight(self):
        while not self.i2c.try_lock():
            pass
        try:
            found = self.i2c.scan()
        finally:
            self.i2c.unlock()
        if 0x30 in found:
            return 0x30
        if 0x62 in found:
            return 0x62
        return None

    def _init_display(self):
        time.sleep(0.05)
        for _ in range(3):
            self._command(0x28)  # function set: 2 lines
            time.sleep(0.005)
        self._command(0x0C)      # display on, cursor off, blink off
        self.clear()
        self._command(0x06)      # entry mode: left to right

    # ---------- display control ----------

    def clear(self):
        self._command(0x01)
        time.sleep(0.005)

    def home(self):
        self._command(0x02)
        time.sleep(0.005)

    def set_cursor(self, col, row):
        row = min(row, self.rows - 1)
        self._command(0x80 | (col + _ROW_OFFSETS[row]))

    def display(self, on=True):
        """Turn the text on or off without erasing it."""
        self._command(0x0C if on else 0x08)

    def cursor(self, show=True, blink=False):
        self._command(0x0C | (0x02 if show else 0) | (0x01 if blink else 0))

    # ---------- text ----------

    def print(self, text):
        """Write text at the current cursor position."""
        for ch in str(text):
            self._write(self.lcd_addr, [0x40, ord(ch) & 0xFF])

    def write_line(self, row, text):
        """Overwrite a whole row, padding/truncating to the width.

        Avoids the flicker of clear() when updating a changing value.
        """
        self.set_cursor(0, row)
        self.print("{:<{w}}".format(str(text)[: self.cols], w=self.cols))

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, text):
        """Clear the screen and show text; use \\n to start a new row."""
        self._message = str(text)
        self.clear()
        for row, line in enumerate(self._message.split("\n")[: self.rows]):
            self.set_cursor(0, row)
            self.print(line[: self.cols])

    _message = ""

    def create_char(self, location, pattern):
        """Define a custom character (location 0-7, pattern = 8 row bytes)."""
        self._command(0x40 | ((location & 0x07) << 3))
        for row in pattern:
            self._write(self.lcd_addr, [0x40, row & 0x1F])
        self.set_cursor(0, 0)

    # ---------- backlight ----------

    def set_backlight(self, r, g, b):
        if self.rgb_addr is None:
            return  # monochrome module
        if self.rgb_addr == 0x30:
            self._write(0x30, [0x00, 0x07])  # reset
            time.sleep(0.001)
            self._write(0x30, [0x04, 0x15])  # LEDs always on
            self._write(0x30, [0x06, r])
            self._write(0x30, [0x07, g])
            self._write(0x30, [0x08, b])
        else:
            self._write(0x62, [0x00, 0x00])
            self._write(0x62, [0x01, 0x00])
            self._write(0x62, [0x08, 0xAA])
            self._write(0x62, [0x04, r])
            self._write(0x62, [0x03, g])
            self._write(0x62, [0x02, b])
