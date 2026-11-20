#!/usr/bin/env python3
"""The World Today -- Thursday 19 November 2026, in one picture.

A single-page newspaper front drawn entirely at runtime with the
Python standard library only (zlib + struct encode the PNG; no
network, no clock, no randomness), so two runs write byte-identical
files.

Every story below was checked against reporting of the day
(19 November 2026) before this page was drawn:

  Lead. Grand Theft Auto VI launches today after a 13-year wait;
     gamers return to Vice City (Rockstar / AP / Le Monde).
  1. Trump, Xi and Putin hold a first three-way summit in
     Shenzhen on the sidelines of APEC; they pledge talks on
     nuclear risk reduction (WSJ / Reuters / Le Monde).
  2. The International Court of Justice rules Myanmar committed
     genocide against the Rohingya -- the first time the World
     Court has held a state responsible for genocide (Reuters).
  3. Iran strikes US bases in Kuwait and Bahrain after the US
     hit a missile site on Qeshm Island (WSJ / BBC).
  4. Nvidia doubles quarterly revenue to $115.8bn in its first
     results since Jensen Huang resigned on 12 November; the
     outlook assumes no China data-center compute revenue
     (Nvidia release, 17 November).
  5. Anthropic prices the largest IPO ever: 980m shares at $83
     raise $81.3bn, valuing the Claude maker near $1.5tn;
     trading starts today on Nasdaq as ANT (CNN / Renaissance).
  6. NASA confirms Voyager 1 has passed one light-day from
     Earth, 49 years after its 1977 launch (Reuters / NASA).
  7. The EU proposes a 45 billion euro loan for Ukraine, repaid
     only once Russia pays war reparations (Reuters, 18 Nov).
  8. Severe Cyclonic Storm Akvan bears down on India's east
     coast, set to cross between Machilipatnam and Puri by noon
     on 20 November (India Meteorological Department).
  Also today: Fed minutes point to more rate hikes; House
  Democrats nominate Hakeem Jeffries for Speaker; Ben Duckett's
  133 beats Australia in the ODI decider; Australia sanctions
  West Bank settlers.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# ------------------------------------------------------------------ palette
PAPER = (247, 242, 230)
PAPER_DEEP = (238, 230, 212)
INK = (18, 18, 18)
CARD = (253, 252, 247)
CARD_SHADE = (243, 240, 230)
SHADOW = (196, 188, 168)
CRIMSON = (178, 28, 34)
CRIMSON_DARK = (132, 18, 24)
DEEPBLUE = (24, 58, 96)
DEEPBLUE_DARK = (14, 36, 62)
FOREST = (16, 102, 86)
FOREST_DARK = (10, 68, 56)
AMBER = (206, 148, 28)
AMBER_LIGHT = (240, 196, 84)
TANGERINE = (226, 106, 26)
PINK = (232, 122, 148)
SKYBLUE = (112, 168, 208)
SKY_TOP = (38, 74, 128)
SKY_MID = (112, 140, 196)
SUNSET = (246, 168, 72)
SLATE = (108, 102, 90)
SOFTGREY = (62, 58, 50)
GOLD_DARK = (150, 104, 10)
PURPLE = (52, 44, 96)
TEAL = (18, 96, 130)


def blend(a, b, t):
    """Linear blend between two RGB colours, t in [0, 1]."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------ hand-cut font
# 5 wide x 7 tall bitmaps, drawn for this page. "#" is ink.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}


def measure(text, size):
    """Pixel width of text at the given bitmap scale."""
    if not text:
        return 0
    return len(text) * 6 * size - size


def fit_lines(text, size, limit):
    """Greedy word wrap into lines no wider than limit pixels."""
    out = []
    for chunk in text.split("\n"):
        current = ""
        for word in chunk.split(" "):
            trial = word if not current else current + " " + word
            if measure(trial, size) <= limit or not current:
                current = trial
            else:
                out.append(current)
                current = word
        if current:
            out.append(current)
    return out


# --------------------------------------------------------------------- board
class Board:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = colour[0]
            self.buf[i + 1] = colour[1]
            self.buf[i + 2] = colour[2]

    def fill(self, x, y, w, h, colour):
        row = bytes(colour) * w
        for yy in range(max(y, 0), min(y + h, self.h)):
            i = (yy * self.w + max(x, 0)) * 3
            span = min(x + w, self.w) - max(x, 0)
            if span > 0:
                self.buf[i:i + span * 3] = row[:span * 3]

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient, one solid row at a time."""
        for k in range(h):
            t = k / max(h - 1, 1)
            self.fill(x, y + k, w, 1, blend(top, bottom, t))

    def hgrad(self, x, y, w, h, left, right):
        """Horizontal gradient, one solid column at a time."""
        for k in range(w):
            t = k / max(w - 1, 1)
            self.fill(x + k, y, 1, h, blend(left, right, t))

    def shadow(self, x, y, w, h, dx=5, dy=5):
        """Soft drop shadow: two offset layers behind a card."""
        self.fill(x + dx, y + dy, w, h, blend(SHADOW, PAPER_DEEP, 0.35))
        self.fill(x + dx // 2, y + dy // 2, w, h, blend(SHADOW, PAPER, 0.45))

    def rule_h(self, x, y, w, colour, thick=1):
        self.fill(x, y, w, thick, colour)

    def rule_v(self, x, y, h, colour, thick=1):
        self.fill(x, y, thick, h, colour)

    def segment(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line with a square brush."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill(x0, y0, thick, thick, colour)
            if x0 == x1 and y0 == y1:
                return
            step = 2 * err
            if step >= dy:
                err += dy
                x0 += sx
            if step <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, colour):
        """Filled circle, scanline by scanline."""
        for dy in range(-r, r + 1):
            half = int(math.sqrt(max(r * r - dy * dy, 0)))
            self.fill(cx - half, cy + dy, half * 2 + 1, 1, colour)

    def shaded_disc(self, cx, cy, r, light, dark):
        """Circle with a light upper-left and dark lower-right."""
        for dy in range(-r, r + 1):
            half = int(math.sqrt(max(r * r - dy * dy, 0)))
            for dx in range(-half, half + 1):
                t = 0.5 + (dx + dy) / (2.6 * max(r, 1))
                self.put(cx + dx, cy + dy, blend(light, dark, min(max(t, 0.0), 1.0)))

    def ring(self, cx, cy, r, colour, thick=3):
        """Circle outline, drawn as small squares along the arc."""
        steps = max(24, r * 4)
        for k in range(steps):
            a = 2 * math.pi * k / steps
            self.fill(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                      thick, thick, colour)

    def arc(self, cx, cy, r, a0, a1, colour, thick=4):
        """Arc from angle a0 to a1 (radians)."""
        n = max(8, int(abs(a1 - a0) * r / 3))
        for k in range(n + 1):
            a = a0 + (a1 - a0) * k / n
            self.fill(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                      thick, thick, colour)

    def triangle(self, pts, colour):
        """Scanline-filled polygon."""
        top = min(p[1] for p in pts)
        bottom = max(p[1] for p in pts)
        for y in range(top, bottom + 1):
            hits = []
            for i in range(len(pts)):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % len(pts)]
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    hits.append(ax + t * (bx - ax))
            hits.sort()
            for i in range(0, len(hits) - 1, 2):
                self.fill(int(hits[i]), y, int(hits[i + 1]) - int(hits[i]) + 1, 1, colour)

    def burst(self, cx, cy, r_out, r_in, spikes, colour):
        """Starburst: alternating long/short points around a centre."""
        pts = []
        for i in range(spikes * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / spikes - math.pi / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.triangle(pts, colour)

    def draw_text(self, x, y, text, size, colour):
        pen = x
        for ch in text:
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.fill(pen + col * size, y + row * size,
                                  size, size, colour)
            pen += 6 * size

    def draw_bold(self, x, y, text, size, colour):
        """Bold by stamping the glyphs with a small cross offset."""
        step = max(1, size // 3)
        for ox, oy in ((0, 0), (step, 0), (0, step), (step, step)):
            self.draw_text(x + ox, y + oy, text, size, colour)

    def draw_centred(self, y, text, size, colour, mid=512):
        self.draw_text(mid - measure(text, size) // 2, y, text, size, colour)

    def draw_centred_bold(self, y, text, size, colour, mid=512):
        self.draw_bold(mid - measure(text, size) // 2, y, text, size, colour)

    def frame(self, x, y, w, h, colour, thick=2):
        self.rule_h(x, y, w, colour, thick)
        self.rule_h(x, y + h - thick, w, colour, thick)
        self.rule_v(x, y, h, colour, thick)
        self.rule_v(x + w - thick, y, h, colour, thick)

    def speckle(self, x, y, w, h, colour, count, seed=20261119):
        """Deterministic paper grain from a tiny linear generator."""
        state = seed
        for _ in range(count):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            px = x + state % max(w, 1)
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            py = y + state % max(h, 1)
            self.put(px, py, colour)


# --------------------------------------------------------------- pictograms
def draw_gta(b, x, y, w, h):
    """Vice City at dusk: gradient sky, lit skyline, palm, controller."""
    # sunset sky: deep blue melting through pink to amber
    for k in range(h):
        t = k / max(h - 1, 1)
        if t < 0.5:
            col = blend(SKY_TOP, PINK, t * 2)
        else:
            col = blend(PINK, SUNSET, (t - 0.5) * 2)
        b.fill(x, y + k, w, 1, col)
    # low sun with a soft glow
    sx, sy = x + int(0.72 * w), y + int(0.30 * h)
    b.disc(sx, sy, int(0.20 * h), blend(SUNSET, PINK, 0.4))
    b.shaded_disc(sx, sy, int(0.14 * h), AMBER_LIGHT, TANGERINE)
    # distant hills, then the skyline
    base = y + int(0.86 * h)
    b.triangle([(x, base), (x + int(0.30 * w), y + int(0.52 * h)),
                (x + int(0.55 * w), base)], blend(DEEPBLUE, PINK, 0.35))
    heights = (0.38, 0.58, 0.32, 0.52, 0.28, 0.44, 0.36)
    tw = int(0.085 * w)
    for i, hf in enumerate(heights):
        tx = x + int(0.03 * w) + i * (tw + 4)
        th = int(hf * h)
        b.fill(tx, base - th, tw, th, DEEPBLUE_DARK)
        b.fill(tx, base - th, max(tw // 3, 2), th, DEEPBLUE)
        for wy in range(4):
            for wx in range(2):
                if (i + wy + wx) % 3:
                    b.fill(tx + 3 + wx * (tw // 2), base - th + 6 + wy * 11,
                           3, 3, AMBER_LIGHT)
    # boulevard with lane dashes
    b.fill(x, base, w, h - int(0.86 * h), (44, 44, 52))
    for k in range(6):
        b.fill(x + 8 + k * int(0.16 * w), base + int(0.05 * h),
               int(0.08 * w), 3, AMBER_LIGHT)
    # palm tree, right of the towers
    px = x + int(0.66 * w)
    top = base - int(0.44 * h)
    b.segment(px, base, px + 4, top + 18, (84, 62, 40), 5)
    b.segment(px + 4, top + 18, px + 12, top, (84, 62, 40), 4)
    for dx, dy in ((-26, -8), (-20, -20), (-6, -26), (10, -24), (22, -14), (26, -2)):
        b.segment(px + 12, top, px + 12 + dx, top + dy, FOREST, 4)
        b.segment(px + 12, top, px + 12 + dx // 2, top + dy // 2,
                  blend(FOREST, AMBER_LIGHT, 0.3), 2)
    b.disc(px + 14, top + 2, 4, (84, 62, 40))
    # controller, bottom right, shaded with a shadow
    cx, cy = x + int(0.84 * w), y + int(0.74 * h)
    b.fill(cx - 30, cy - 8, 64, 26, SHADOW)
    b.fill(cx - 34, cy - 12, 64, 26, CARD)
    b.fill(cx - 34, cy + 8, 64, 6, CARD_SHADE)
    b.frame(cx - 34, cy - 12, 64, 26, INK, 2)
    b.shaded_disc(cx - 18, cy + 1, 5, PINK, CRIMSON)
    b.shaded_disc(cx + 16, cy + 1, 5, SKYBLUE, DEEPBLUE)
    b.fill(cx - 4, cy - 5, 8, 3, INK)
    b.fill(cx - 1, cy - 8, 3, 8, INK)


def draw_summit(b, x, y, s):
    """Three flags over a summit table: US, China, Russia."""
    # Great Wall ridge behind the flags
    b.triangle([(x, y + int(0.62 * s)), (x + int(0.30 * s), y + int(0.30 * s)),
                (x + int(0.55 * s), y + int(0.48 * s)),
                (x + int(0.80 * s), y + int(0.26 * s)),
                (x + s, y + int(0.62 * s))], blend(DEEPBLUE, CARD, 0.72))
    for i, (fx, flag) in enumerate((
            (int(0.12 * s), "us"), (int(0.42 * s), "cn"), (int(0.72 * s), "ru"))):
        px = x + fx
        top = y + int(0.08 * s)
        b.fill(px - 2, top, 4, int(0.60 * s), INK)
        b.shaded_disc(px, top - 2, 4, AMBER_LIGHT, AMBER)
        fw, fh = int(0.26 * s), int(0.18 * s)
        if flag == "us":
            b.fill(px + 2, top + 4, fw, fh, CRIMSON)
            for k in range(3):
                b.fill(px + 2, top + 8 + k * 7, fw, 3, CARD)
            b.fill(px + 2, top + 4, fw // 2, fh // 2, DEEPBLUE)
            b.fill(px + 5, top + 6, 3, 3, CARD)
            b.fill(px + 11, top + 6, 3, 3, CARD)
        elif flag == "cn":
            b.fill(px + 2, top + 4, fw, fh, CRIMSON)
            b.burst(px + 10, top + 12, 6, 3, 5, AMBER)
            b.burst(px + 19, top + 8, 3, 2, 5, AMBER)
        else:
            b.fill(px + 2, top + 4, fw, fh // 3 + 1, CARD)
            b.fill(px + 2, top + 4 + fh // 3, fw, fh // 3 + 1, DEEPBLUE)
            b.fill(px + 2, top + 4 + 2 * fh // 3, fw, fh // 3 + 1, CRIMSON)
        b.fill(px + 2, top + 4 + fh - 3, fw, 3, blend(INK, CARD, 0.55))
    # summit table with orchids
    b.fill(x + int(0.06 * s) + 3, y + int(0.72 * s) + 3, int(0.88 * s), 8, SHADOW)
    b.fill(x + int(0.06 * s), y + int(0.72 * s), int(0.88 * s), 8, (84, 58, 36))
    b.fill(x + int(0.06 * s), y + int(0.72 * s), int(0.88 * s), 3, (120, 86, 52))
    b.fill(x + int(0.12 * s), y + int(0.80 * s), 6, int(0.16 * s), INK)
    b.fill(x + int(0.82 * s), y + int(0.80 * s), 6, int(0.16 * s), INK)
    b.shaded_disc(x + int(0.50 * s), y + int(0.66 * s), 7, PINK, CRIMSON)
    b.disc(x + int(0.44 * s), y + int(0.68 * s), 4, PINK)
    b.disc(x + int(0.56 * s), y + int(0.68 * s), 4, PINK)


def draw_court(b, x, y, s):
    """The World Court: pediment, pillars and the scales of justice."""
    cx = x + s // 2
    # pediment and roof line
    b.triangle([(x + int(0.08 * s), y + int(0.22 * s)),
                (cx, y + int(0.06 * s)),
                (x + int(0.92 * s), y + int(0.22 * s))], DEEPBLUE_DARK)
    b.fill(x + int(0.06 * s), y + int(0.22 * s), int(0.88 * s), 5, INK)
    b.shaded_disc(cx, y + int(0.17 * s), 5, AMBER_LIGHT, AMBER)
    # pillars with shading
    for k in range(4):
        px = x + int(0.14 * s) + k * int(0.20 * s)
        b.fill(px, y + int(0.28 * s), int(0.09 * s), int(0.46 * s), CARD_SHADE)
        b.fill(px, y + int(0.28 * s), 3, int(0.46 * s), CARD)
        b.fill(px + int(0.09 * s) - 3, y + int(0.28 * s), 3,
               int(0.46 * s), blend(CARD_SHADE, INK, 0.18))
        b.fill(px - 2, y + int(0.28 * s), int(0.09 * s) + 4, 4, INK)
        b.fill(px - 2, y + int(0.74 * s) - 4, int(0.09 * s) + 4, 4, INK)
    # steps
    b.fill(x + int(0.04 * s), y + int(0.76 * s), int(0.92 * s), 5, INK)
    b.fill(x + int(0.08 * s), y + int(0.82 * s), int(0.84 * s), 5, SLATE)
    # scales held in front of the pillars
    sy = y + int(0.36 * s)
    b.fill(cx - 2, sy, 4, int(0.30 * s), GOLD_DARK)
    b.fill(cx - int(0.30 * s), sy, int(0.60 * s), 4, GOLD_DARK)
    b.shaded_disc(cx, sy + 2, 5, AMBER_LIGHT, AMBER)
    for side in (-1, 1):
        bx = cx + side * int(0.28 * s)
        b.segment(bx, sy + 2, bx - 8, sy + int(0.16 * s), GOLD_DARK, 2)
        b.segment(bx, sy + 2, bx + 8, sy + int(0.16 * s), GOLD_DARK, 2)
        b.arc(bx, sy + int(0.16 * s), 10, 0.15, math.pi - 0.15, AMBER, 4)
    b.fill(cx - 10, sy + int(0.30 * s), 20, 4, GOLD_DARK)


def draw_gulf(b, x, y, s):
    """Gulf waters: a ship, a missile trail, a burst over an island."""
    # gradient sea with wave caps
    b.vgrad(x, y + int(0.74 * s), s, int(0.24 * s), SKYBLUE, DEEPBLUE)
    for k in range(3):
        yy = y + int(0.80 * s) + k * int(0.06 * s)
        for xx in range(x, x + s, 16):
            b.segment(xx, yy, xx + 8, yy - 5, CARD, 2)
    # island with a burst
    b.triangle([(x + int(0.58 * s), y + int(0.74 * s)),
                (x + int(0.72 * s), y + int(0.58 * s)),
                (x + int(0.86 * s), y + int(0.74 * s))], (96, 140, 90))
    b.triangle([(x + int(0.66 * s), y + int(0.74 * s)),
                (x + int(0.72 * s), y + int(0.58 * s)),
                (x + int(0.86 * s), y + int(0.74 * s))], (74, 114, 70))
    b.burst(x + int(0.72 * s), y + int(0.44 * s), int(0.22 * s),
            int(0.10 * s), 8, AMBER)
    b.burst(x + int(0.72 * s), y + int(0.44 * s), int(0.12 * s),
            int(0.05 * s), 8, TANGERINE)
    b.disc(x + int(0.72 * s), y + int(0.44 * s), 4, AMBER_LIGHT)
    # ship, left, with a shaded hull
    sx = x + int(0.04 * s)
    sy = y + int(0.66 * s)
    b.triangle([(sx, sy), (sx + int(0.44 * s), sy),
                (sx + int(0.36 * s), sy + int(0.10 * s)),
                (sx + int(0.06 * s), sy + int(0.10 * s))], SLATE)
    b.triangle([(sx, sy), (sx + int(0.44 * s), sy),
                (sx + int(0.40 * s), sy + int(0.05 * s)),
                (sx + int(0.04 * s), sy + int(0.05 * s))],
               blend(SLATE, CARD, 0.35))
    b.fill(sx + int(0.10 * s), sy - int(0.12 * s), int(0.16 * s),
           int(0.12 * s), INK)
    b.fill(sx + int(0.10 * s), sy - int(0.12 * s), int(0.16 * s), 3,
           blend(INK, CARD, 0.4))
    b.fill(sx + int(0.16 * s), sy - int(0.24 * s), 4, int(0.12 * s), INK)
    # missile trail arcing from the ship toward the island
    b.arc(x + int(0.30 * s), y + int(0.62 * s), int(0.34 * s),
          -1.2, 0.5, CRIMSON, 4)
    b.arc(x + int(0.30 * s), y + int(0.62 * s), int(0.34 * s),
          -1.2, -0.4, blend(CRIMSON, CARD, 0.4), 2)
    b.disc(x + int(0.60 * s), y + int(0.34 * s), 5, CRIMSON)


def draw_chip(b, x, y, s):
    """AI chip with pins and a rising market arrow."""
    cx, cy = x + int(0.46 * s), y + int(0.48 * s)
    side = int(0.50 * s)
    # shadow, then the package with a two-tone die
    b.fill(cx - side // 2 + 4, cy - side // 2 + 4, side, side, SHADOW)
    b.fill(cx - side // 2, cy - side // 2, side, side, FOREST_DARK)
    b.fill(cx - side // 2, cy - side // 2, side, side // 2, FOREST)
    b.fill(cx - side // 2 + 9, cy - side // 2 + 9, side - 18, side - 18,
           (44, 148, 120))
    b.fill(cx - side // 2 + 9, cy - side // 2 + 9, side - 18, (side - 18) // 2,
           (64, 168, 138))
    b.fill(cx - 11, cy - 11, 22, 22, AMBER)
    b.fill(cx - 11, cy - 11, 22, 6, AMBER_LIGHT)
    b.frame(cx - 11, cy - 11, 22, 22, GOLD_DARK, 2)
    for k in range(5):
        off = -side // 2 + 8 + k * (side - 16) // 4
        b.fill(cx + off - 2, cy - side // 2 - 11, 4, 11, INK)
        b.fill(cx + off - 2, cy + side // 2, 4, 11, INK)
        b.fill(cx - side // 2 - 11, cy + off - 2, 11, 4, INK)
        b.fill(cx + side // 2, cy + off - 2, 11, 4, INK)
    # rising arrow, bottom left, with a soft underlay
    ax = x + int(0.04 * s)
    ay = y + int(0.92 * s)
    b.segment(ax + 2, ay + 2, ax + int(0.16 * s) + 2, ay - int(0.18 * s) + 2,
              SHADOW, 5)
    b.segment(ax, ay, ax + int(0.16 * s), ay - int(0.18 * s), CRIMSON, 5)
    b.segment(ax + int(0.16 * s), ay - int(0.18 * s),
              ax + int(0.34 * s), ay - int(0.40 * s), CRIMSON, 5)
    b.triangle([(ax + int(0.34 * s), ay - int(0.40 * s)),
                (ax + int(0.26 * s), ay - int(0.40 * s)),
                (ax + int(0.34 * s), ay - int(0.30 * s))], CRIMSON)


def draw_ipo(b, x, y, s):
    """IPO day: a trading bell over rising bars."""
    cx = x + s // 2
    # rising bars behind the bell
    base = y + int(0.88 * s)
    for k, hf in enumerate((0.22, 0.36, 0.52, 0.70)):
        bx = x + int(0.08 * s) + k * int(0.22 * s)
        bh = int(hf * s)
        col = blend(DEEPBLUE, FOREST, k / 3)
        b.fill(bx, base - bh, int(0.15 * s), bh, col)
        b.fill(bx, base - bh, int(0.15 * s), 4, blend(col, CARD, 0.45))
    b.fill(x + int(0.04 * s), base, int(0.92 * s), 4, INK)
    # the bell, shaded gold, rung at the open
    by = y + int(0.30 * s)
    b.fill(cx - 3, by - int(0.16 * s), 6, int(0.16 * s), GOLD_DARK)
    b.shaded_disc(cx, by - int(0.18 * s), 6, AMBER_LIGHT, AMBER)
    b.triangle([(cx - int(0.26 * s), by + int(0.18 * s)),
                (cx - int(0.14 * s), by - int(0.08 * s)),
                (cx + int(0.14 * s), by - int(0.08 * s)),
                (cx + int(0.26 * s), by + int(0.18 * s))], AMBER)
    b.triangle([(cx - int(0.26 * s), by + int(0.18 * s)),
                (cx - int(0.14 * s), by - int(0.08 * s)),
                (cx, by - int(0.08 * s)),
                (cx, by + int(0.18 * s))], AMBER_LIGHT)
    b.fill(cx - int(0.28 * s), by + int(0.18 * s), int(0.56 * s), 5, GOLD_DARK)
    b.shaded_disc(cx, by + int(0.27 * s), 6, AMBER_LIGHT, GOLD_DARK)
    # sound arcs either side
    b.arc(cx, by, int(0.32 * s), -2.6, -1.9, CRIMSON, 4)
    b.arc(cx, by, int(0.32 * s), -1.2, -0.5, CRIMSON, 4)


def draw_probe(b, x, y, s):
    """Voyager: gold bus, solar panels, dish, signal rings, stars."""
    # deep-space panel behind the probe
    b.vgrad(x, y, s, int(0.92 * s), (16, 20, 44), (36, 44, 84))
    for sx, sy, r in ((0.10, 0.10, 3), (0.90, 0.08, 4), (0.94, 0.32, 3),
                      (0.06, 0.40, 3), (0.86, 0.60, 3), (0.16, 0.66, 2),
                      (0.70, 0.12, 2)):
        b.disc(x + int(sx * s), y + int(sy * s), r, AMBER_LIGHT)
    cx, cy = x + int(0.46 * s), y + int(0.66 * s)
    # dish: a shallow bowl on a mast above the bus
    b.segment(cx, cy - 12, cx, cy - int(0.28 * s), CARD, 4)
    b.arc(cx, cy - int(0.28 * s) - 4, 26, 0.25, math.pi - 0.25, SKYBLUE, 5)
    b.arc(cx, cy - int(0.28 * s) - 4, 20, 0.35, math.pi - 0.35,
          blend(SKYBLUE, CARD, 0.5), 3)
    b.segment(cx - 24, cy - int(0.28 * s) - 12, cx, cy - 12, CARD, 3)
    b.segment(cx + 24, cy - int(0.28 * s) - 12, cx, cy - 12, CARD, 3)
    # signal arcs from the dish, fading with distance
    b.arc(cx, cy - int(0.28 * s) - 4, 26, -2.4, -0.7, AMBER, 4)
    b.arc(cx, cy - int(0.28 * s) - 4, 33, -2.4, -0.7,
          blend(AMBER, (36, 44, 84), 0.45), 4)
    # gold bus body with blue solar panels
    b.fill(cx - 36, cy - 6, 30, 12, DEEPBLUE)
    b.fill(cx - 36, cy - 6, 30, 4, SKYBLUE)
    b.fill(cx + 6, cy - 6, 30, 12, DEEPBLUE)
    b.fill(cx + 6, cy - 6, 30, 4, SKYBLUE)
    b.fill(cx - 14, cy - 12, 28, 26, AMBER)
    b.fill(cx - 14, cy - 12, 28, 7, AMBER_LIGHT)
    b.frame(cx - 14, cy - 12, 28, 26, INK, 2)
    b.fill(cx - 8, cy - 5, 16, 4, INK)
    b.fill(cx - 8, cy + 3, 16, 4, INK)
    # the Golden Record, bottom right
    px, py = x + int(0.84 * s), y + int(0.80 * s)
    b.shaded_disc(px, py, 12, AMBER_LIGHT, GOLD_DARK)
    b.ring(px, py, 12, GOLD_DARK, 2)
    b.disc(px, py, 3, INK)
    b.segment(px - 20, py + 10, px + 20, py - 10, AMBER, 2)


def draw_euro(b, x, y, s):
    """A gold euro coin ringed by the EU's circle of stars."""
    cx, cy = x + s // 2, y + int(0.46 * s)
    # deep-blue field behind the coin
    b.fill(x, y, s, int(0.92 * s), (20, 70, 140))
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        b.burst(int(cx + int(0.40 * s) * math.cos(a)),
                int(cy + int(0.40 * s) * math.sin(a)), 6, 3, 5, AMBER_LIGHT)
    b.shaded_disc(cx, cy, int(0.28 * s), (246, 208, 110), GOLD_DARK)
    b.ring(cx, cy, int(0.28 * s), GOLD_DARK, 3)
    b.disc(cx, cy, int(0.20 * s), (232, 184, 64))
    b.draw_bold(cx - 12, cy - 17, "E", 5, DEEPBLUE_DARK)
    # coin stack at the base
    for k in range(3):
        b.fill(x + int(0.14 * s) + k * 6, y + int(0.88 * s) - k * 7,
               int(0.30 * s), 6, AMBER)
        b.fill(x + int(0.14 * s) + k * 6, y + int(0.88 * s) - k * 7,
               int(0.30 * s), 2, AMBER_LIGHT)


def draw_storm(b, x, y, s):
    """Cyclone Akvan: spiral bands, rain, sea swell."""
    cx, cy = x + s // 2, y + int(0.40 * s)
    # cloud disc behind the spiral
    b.shaded_disc(cx, cy, int(0.44 * s), blend(SKYBLUE, CARD, 0.55), SKYBLUE)
    for k, r in enumerate((12, 22, 32, 42)):
        b.arc(cx, cy, r, -0.5 + k * 0.8, 4.4 + k * 0.8,
              blend(DEEPBLUE, CARD, k * 0.16), 5)
    b.disc(cx, cy, 7, AMBER)
    b.disc(cx, cy, 3, AMBER_LIGHT)
    # rain, diagonal streaks
    for k in range(4):
        xx = x + int(0.10 * s) + k * int(0.20 * s)
        b.segment(xx, y + int(0.76 * s), xx - 8, y + int(0.92 * s),
                  SKYBLUE, 3)
    # swell over a gradient sea strip
    b.vgrad(x, y + int(0.88 * s), s, int(0.10 * s), SKYBLUE, DEEPBLUE)
    b.arc(x + int(0.50 * s), y + int(1.02 * s), int(0.30 * s),
          math.pi * 1.15, math.pi * 1.85, DEEPBLUE, 4)


# -------------------------------------------------------------------- layout
STORIES = [
    dict(tag="SHENZHEN", colour=DEEPBLUE,
         head="TRUMP, XI, PUTIN\nMEET IN SHENZHEN",
         body="FIRST THREE-WAY SUMMIT\nPLEDGES NUCLEAR RISK\nTALKS AT APEC TODAY",
         pic=draw_summit),
    dict(tag="THE HAGUE", colour=(96, 40, 64),
         head="UN COURT: MYANMAR\nCOMMITTED GENOCIDE",
         body="FIRST STATE HELD GUILTY\nOF GENOCIDE; ROHINGYA\nTO GET REPARATIONS",
         pic=draw_court),
    dict(tag="THE GULF", colour=CRIMSON,
         head="US AND IRAN TRADE\nFIRE IN THE GULF",
         body="IRAN HITS BASES IN\nKUWAIT AND BAHRAIN;\nUS STRUCK QESHM SITE",
         pic=draw_gulf),
    dict(tag="MARKETS", colour=FOREST,
         head="NVIDIA DOUBLES\nSALES TO $115.8BN",
         body="FIRST RESULTS SINCE\nHUANG RESIGNED; NO\nCHINA SALES IN OUTLOOK",
         pic=draw_chip),
    dict(tag="WALL STREET", colour=(140, 96, 20),
         head="ANTHROPIC IPO\nRAISES $81.3BN",
         body="SHARES AT $83 VALUE AI\nFIRM NEAR $1.5TN; ANT\nSTARTS TRADING TODAY",
         pic=draw_ipo),
    dict(tag="SPACE", colour=PURPLE,
         head="VOYAGER 1 REACHES\nONE LIGHT-DAY OUT",
         body="49 YEARS ON, THE PROBE\nIS 16BN MILES AWAY,\nNASA CONFIRMS TODAY",
         pic=draw_probe),
    dict(tag="EUROPE", colour=(20, 70, 140),
         head="EU PLANS 45BN EURO\nLOAN FOR UKRAINE",
         body="KYIV GETS 45BN EUROS;\nREPAYMENT ONLY AFTER\nRUSSIA PAYS UP",
         pic=draw_euro),
    dict(tag="INDIA", colour=TEAL,
         head="CYCLONE AKVAN\nNEARS INDIA COAST",
         body="SEVERE STORM TO CROSS\nBETWEEN MACHILIPATNAM\nAND PURI ON 20 NOV",
         pic=draw_storm),
]


def compose():
    b = Board(PAGE_W, PAGE_H, PAPER)
    # gentle vertical paper gradient, then grain over the whole sheet
    b.vgrad(0, 0, PAGE_W, PAGE_H, PAPER, PAPER_DEEP)
    b.speckle(8, 8, PAGE_W - 16, PAGE_H - 16,
              blend(PAPER_DEEP, INK, 0.10), 2600)
    # outer frame, double-ruled like a broadsheet
    b.frame(0, 0, PAGE_W, PAGE_H, INK, 6)
    b.frame(12, 12, PAGE_W - 24, PAGE_H - 24, INK, 2)

    # ---- masthead: the biggest type on the page
    b.draw_centred_bold(18, "THE WORLD TODAY", 10, INK)
    b.rule_h(24, 92, 976, CRIMSON, 6)
    b.rule_h(24, 100, 976, INK, 2)
    b.draw_centred_bold(108, "THURSDAY, 19 NOVEMBER 2026", 4, CRIMSON_DARK)
    b.draw_text(24, 108, "ONE IMAGE", 2, SOFTGREY)
    b.draw_text(1000 - measure("EIGHT STORIES", 2), 108, "EIGHT STORIES", 2,
                SOFTGREY)
    b.rule_h(24, 140, 976, INK, 3)

    # ---- lead story: GTA VI, with a full-bleed sunset illustration
    lx, ly, lw, lh = 24, 152, 976, 188
    b.shadow(lx, ly, lw, lh)
    b.fill(lx, ly, lw, lh, CARD)
    b.hgrad(lx, ly, lw, 30, CRIMSON, CRIMSON_DARK)
    b.draw_bold(lx + 16, ly + 6, "LEAD STORY - GAMING", 3, CARD)
    b.draw_text(lx + lw - 16 - measure("VICE CITY", 3), ly + 7, "VICE CITY",
                3, CARD)
    b.draw_bold(lx + 20, ly + 37, "GTA VI IS HERE", 6, INK)
    b.draw_bold(lx + 20, ly + 86, "VICE CITY OPENS", 6, CRIMSON_DARK)
    lead = ("AFTER A 13-YEAR WAIT, ROCKSTAR'S BLOCKBUSTER "
            "BEGINS ITS GLOBAL ROLLOUT TODAY AS GAMERS "
            "FLOOD BACK TO VICE CITY")
    for i, line in enumerate(fit_lines(lead, 2, 600)):
        b.draw_text(lx + 20, ly + 136 + i * 16, line, 2, SOFTGREY)
    draw_gta(b, lx + 648, ly + 36, 308, 140)
    b.frame(lx, ly, lw, lh, INK, 3)

    # ---- eight story cards, 2 columns x 4 rows
    pw, ph = 482, 132
    for idx, story in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        px = 24 + col * (pw + 12)
        py = 348 + row * (ph + 6)
        b.shadow(px, py, pw, ph, 4, 4)
        b.fill(px, py, pw, ph, CARD)
        b.hgrad(px, py, pw, 24, story["colour"],
                blend(story["colour"], INK, 0.35))
        b.draw_bold(px + 12, py + 5, story["tag"], 2, CARD)
        for i, line in enumerate(story["head"].split("\n")):
            b.draw_bold(px + 14, py + 29 + i * 25, line, 3, INK)
        for i, line in enumerate(story["body"].split("\n")[:3]):
            b.draw_text(px + 14, py + 80 + i * 16, line, 2, SOFTGREY)
        story["pic"](b, px + pw - 104, py + 32, 92)
        b.frame(px, py, pw, ph, INK, 2)

    # ---- footer ticker
    fy = 906
    b.shadow(24, fy, 976, 84, 4, 4)
    b.vgrad(24, fy, 976, 84, DEEPBLUE, DEEPBLUE_DARK)
    b.draw_centred_bold(fy + 12,
                        "ALSO TODAY: FED SEES MORE RATE HIKES - JEFFRIES NOMINATED FOR SPEAKER",
                        2, CARD)
    b.draw_centred(fy + 38,
                   "DUCKETT 133 BEATS AUSTRALIA - AUSTRALIA SANCTIONS SETTLERS",
                   2, (196, 204, 218))
    b.draw_centred(fy + 60, "SOURCES: AP - REUTERS - AFP - BBC - IMD - NASA",
                   2, AMBER_LIGHT)
    b.frame(24, fy, 976, 84, INK, 2)
    return b


# -------------------------------------------------------------- PNG encoder
def encode_png(b):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", PAGE_W, PAGE_H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(PAGE_H):
        raw.append(0)  # filter: none
        raw += b.buf[y * PAGE_W * 3:(y + 1) * PAGE_W * 3]
    body = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", body) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(compose())
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
