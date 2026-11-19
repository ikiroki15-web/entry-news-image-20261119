#!/usr/bin/env python3
"""The World Today -- Thursday 19 November 2026, in one picture.

A single-page newspaper front drawn entirely at runtime with the
Python standard library only (zlib + struct encode the PNG; no
network, no clock, no randomness), so two runs write byte-identical
files.

Stories, all first reported on Thursday 19 November 2026:
  1. GTA VI begins its global rollout; gamers return to Vice City
     after a 13-year wait (AP).
  2. Trump, Xi and Putin meet in Shenzhen at the APEC summit;
     nuclear arms control and Iran top the agenda.
  3. US-Iran fighting widens in the Gulf: Iran strikes US bases in
     Kuwait and Bahrain after the US hit a missile site on
     Qeshm Island.
  4. Nvidia doubles quarterly revenue to $115.84bn in its first
     results since Jensen Huang's ouster; H-series chip shipments
     to mainland China have stopped.
  5. NASA's Voyager 1 reaches one light-day from Earth, 48 years
     after launch; NASA confirms the milestone on 19 November.
  6. The EU proposes a 45 billion euro loan for Ukraine, repaid
     only once Russia pays war reparations (Financial Times).
  7. Cyclone Akvan bears down on India's east coast, set to cross
     between Machilipatnam and Puri.
  Also: Fed minutes point to more rate hikes; Hakeem Jeffries is
  set to become the first Black Speaker of the US House;
  Australia sanctions West Bank settlers; Ben Duckett hits 133
  in the ODI against Australia.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# ------------------------------------------------------------------ palette
PAPER = (247, 242, 230)
INK = (18, 18, 18)
CARD = (253, 252, 247)
CRIMSON = (178, 28, 34)
DEEPBLUE = (24, 58, 96)
FOREST = (16, 102, 86)
AMBER = (206, 148, 28)
TANGERINE = (226, 106, 26)
SKYBLUE = (112, 168, 208)
SLATE = (108, 102, 90)
SOFTGREY = (62, 58, 50)

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

    def draw_centred(self, y, text, size, colour, mid=512):
        self.draw_text(mid - measure(text, size) // 2, y, text, size, colour)

    def frame(self, x, y, w, h, colour, thick=2):
        self.rule_h(x, y, w, colour, thick)
        self.rule_h(x, y + h - thick, w, colour, thick)
        self.rule_v(x, y, h, colour, thick)
        self.rule_v(x + w - thick, y, h, colour, thick)


# --------------------------------------------------------------- pictograms
def draw_gta(b, x, y, s):
    """Vice City at dusk: sun, skyline, palm, game controller."""
    b.disc(x + int(0.82 * s), y + int(0.18 * s), int(0.15 * s), TANGERINE)
    b.disc(x + int(0.82 * s), y + int(0.18 * s), int(0.09 * s), AMBER)
    # skyline on the left, towers of different heights
    base = y + int(0.88 * s)
    heights = (0.42, 0.62, 0.34, 0.55, 0.30, 0.48)
    tw = int(0.085 * s)
    for i, hf in enumerate(heights):
        tx = x + int(0.02 * s) + i * (tw + 3)
        th = int(hf * s)
        b.fill(tx, base - th, tw, th, DEEPBLUE)
        for wy in range(3):
            b.fill(tx + 3, base - th + 6 + wy * 12, tw - 6, 3, AMBER)
    b.fill(x, base, int(0.62 * s), 6, INK)
    # palm tree, right of the towers
    px, py = x + int(0.70 * s), base
    b.segment(px, py, px + 8, py - int(0.40 * s), FOREST, 5)
    for dx, dy in ((-24, -10), (-18, -22), (-4, -26), (10, -24), (20, -14)):
        b.segment(px + 8, py - int(0.40 * s),
                  px + 8 + dx, py - int(0.40 * s) + dy, FOREST, 4)
    b.disc(px + 10, py - int(0.40 * s) - 3, 5, FOREST)
    # controller, bottom right on its own patch of ground
    cx, cy = x + int(0.82 * s), y + int(0.76 * s)
    b.fill(x + int(0.64 * s), base, int(0.36 * s), 6, INK)
    b.fill(cx - 32, cy - 12, 64, 26, CARD)
    b.frame(cx - 32, cy - 12, 64, 26, INK, 2)
    b.disc(cx - 18, cy + 2, 4, CRIMSON)
    b.disc(cx + 18, cy + 2, 4, DEEPBLUE)
    b.fill(cx - 4, cy - 5, 8, 3, INK)
    b.fill(cx - 1, cy - 8, 3, 8, INK)


def draw_summit(b, x, y, s):
    """Three flags over a summit table: US, China, Russia."""
    pole_tops = []
    for i, (fx, flag) in enumerate((
            (int(0.14 * s), "us"), (int(0.44 * s), "cn"), (int(0.74 * s), "ru"))):
        px = x + fx
        top = y + int(0.10 * s)
        pole_tops.append((px, top))
        b.fill(px - 2, top, 4, int(0.58 * s), INK)
        b.disc(px, top - 2, 4, AMBER)
        fw, fh = int(0.26 * s), int(0.18 * s)
        if flag == "us":
            b.fill(px + 2, top + 4, fw, fh, CRIMSON)
            for k in range(3):
                b.fill(px + 2, top + 8 + k * 7, fw, 3, CARD)
            b.fill(px + 2, top + 4, fw // 2, fh // 2, DEEPBLUE)
        elif flag == "cn":
            b.fill(px + 2, top + 4, fw, fh, CRIMSON)
            b.burst(px + 10, top + 12, 6, 3, 5, AMBER)
        else:
            b.fill(px + 2, top + 4, fw, fh // 3 + 1, CARD)
            b.fill(px + 2, top + 4 + fh // 3, fw, fh // 3 + 1, DEEPBLUE)
            b.fill(px + 2, top + 4 + 2 * fh // 3, fw, fh // 3 + 1, CRIMSON)
    # summit table
    b.fill(x + int(0.06 * s), y + int(0.72 * s), int(0.88 * s), 8, INK)
    b.fill(x + int(0.12 * s), y + int(0.80 * s), 6, int(0.16 * s), INK)
    b.fill(x + int(0.82 * s), y + int(0.80 * s), 6, int(0.16 * s), INK)
    b.disc(x + int(0.50 * s), y + int(0.66 * s), 7, AMBER)


def draw_gulf(b, x, y, s):
    """Gulf waters: a ship, a missile trail, a burst over an island."""
    # sea
    b.fill(x, y + int(0.74 * s), s, int(0.24 * s), SKYBLUE)
    for k in range(3):
        yy = y + int(0.80 * s) + k * int(0.06 * s)
        for xx in range(x, x + s, 16):
            b.segment(xx, yy, xx + 8, yy - 5, CARD, 2)
    # island with a burst
    b.triangle([(x + int(0.58 * s), y + int(0.74 * s)),
                (x + int(0.72 * s), y + int(0.58 * s)),
                (x + int(0.86 * s), y + int(0.74 * s))], (96, 140, 90))
    b.burst(x + int(0.72 * s), y + int(0.44 * s), int(0.22 * s),
            int(0.10 * s), 8, AMBER)
    b.burst(x + int(0.72 * s), y + int(0.44 * s), int(0.12 * s),
            int(0.05 * s), 8, TANGERINE)
    # ship, left
    sx = x + int(0.04 * s)
    sy = y + int(0.66 * s)
    b.triangle([(sx, sy), (sx + int(0.44 * s), sy),
                (sx + int(0.36 * s), sy + int(0.10 * s)),
                (sx + int(0.06 * s), sy + int(0.10 * s))], SLATE)
    b.fill(sx + int(0.10 * s), sy - int(0.12 * s), int(0.16 * s), int(0.12 * s), INK)
    b.fill(sx + int(0.16 * s), sy - int(0.24 * s), 4, int(0.12 * s), INK)
    # missile trail arcing from the ship toward the island
    b.arc(x + int(0.30 * s), y + int(0.62 * s), int(0.34 * s),
          -1.2, 0.5, CRIMSON, 4)
    b.disc(x + int(0.60 * s), y + int(0.34 * s), 5, CRIMSON)


def draw_chip(b, x, y, s):
    """AI chip with pins and a rising market arrow."""
    cx, cy = x + int(0.46 * s), y + int(0.50 * s)
    side = int(0.50 * s)
    b.fill(cx - side // 2, cy - side // 2, side, side, FOREST)
    b.fill(cx - side // 2 + 9, cy - side // 2 + 9, side - 18, side - 18,
           (44, 148, 120))
    b.fill(cx - 11, cy - 11, 22, 22, AMBER)
    for k in range(5):
        off = -side // 2 + 8 + k * (side - 16) // 4
        b.fill(cx + off - 2, cy - side // 2 - 11, 4, 11, INK)
        b.fill(cx + off - 2, cy + side // 2, 4, 11, INK)
        b.fill(cx - side // 2 - 11, cy + off - 2, 11, 4, INK)
        b.fill(cx + side // 2, cy + off - 2, 11, 4, INK)
    # rising arrow, bottom left
    ax = x + int(0.04 * s)
    ay = y + int(0.90 * s)
    b.segment(ax, ay, ax + int(0.16 * s), ay - int(0.18 * s), CRIMSON, 5)
    b.segment(ax + int(0.16 * s), ay - int(0.18 * s),
              ax + int(0.34 * s), ay - int(0.40 * s), CRIMSON, 5)
    b.triangle([(ax + int(0.34 * s), ay - int(0.40 * s)),
                (ax + int(0.26 * s), ay - int(0.40 * s)),
                (ax + int(0.34 * s), ay - int(0.30 * s))], CRIMSON)


def draw_probe(b, x, y, s):
    """Voyager: gold bus, solar panels, dish, signal rings, stars."""
    for sx, sy, r in ((0.10, 0.10, 3), (0.90, 0.08, 4), (0.94, 0.32, 3),
                      (0.06, 0.40, 3), (0.86, 0.60, 3)):
        b.disc(x + int(sx * s), y + int(sy * s), r, AMBER)
    cx, cy = x + int(0.46 * s), y + int(0.52 * s)
    # dish: a shallow bowl on a mast above the bus
    b.segment(cx, cy - 12, cx, cy - int(0.30 * s), INK, 4)
    b.arc(cx, cy - int(0.30 * s) - 6, 30, 0.25, math.pi - 0.25, SKYBLUE, 5)
    b.segment(cx - 28, cy - int(0.30 * s) - 14, cx, cy - 12, INK, 3)
    b.segment(cx + 28, cy - int(0.30 * s) - 14, cx, cy - 12, INK, 3)
    # signal arcs from the dish
    b.arc(cx, cy - int(0.30 * s) - 6, 44, -2.4, -0.7, AMBER, 4)
    b.arc(cx, cy - int(0.30 * s) - 6, 58, -2.4, -0.7, AMBER, 4)
    # gold bus body with blue solar panels
    b.fill(cx - 36, cy - 6, 30, 12, DEEPBLUE)
    b.fill(cx + 6, cy - 6, 30, 12, DEEPBLUE)
    b.fill(cx - 14, cy - 12, 28, 26, AMBER)
    b.frame(cx - 14, cy - 12, 28, 26, INK, 2)
    b.fill(cx - 8, cy - 5, 16, 4, INK)
    b.fill(cx - 8, cy + 3, 16, 4, INK)
    # a small ringed planet, bottom right
    px, py = x + int(0.84 * s), y + int(0.82 * s)
    b.disc(px, py, 12, TANGERINE)
    b.segment(px - 20, py + 6, px + 20, py - 6, AMBER, 3)


def draw_euro(b, x, y, s):
    """A gold euro coin ringed by the EU's circle of stars."""
    cx, cy = x + s // 2, y + int(0.48 * s)
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        b.disc(int(cx + int(0.40 * s) * math.cos(a)),
               int(cy + int(0.40 * s) * math.sin(a)), 4, AMBER)
    b.disc(cx, cy, int(0.28 * s), AMBER)
    b.ring(cx, cy, int(0.28 * s), (150, 104, 10), 3)
    b.disc(cx, cy, int(0.20 * s), (232, 184, 64))
    b.draw_text(cx - 11, cy - 17, "E", 5, DEEPBLUE)
    # coin stack at the base
    for k in range(3):
        b.fill(x + int(0.14 * s) + k * 6, y + int(0.86 * s) - k * 7,
               int(0.30 * s), 6, AMBER)


def draw_storm(b, x, y, s):
    """Cyclone Akvan: spiral bands, rain, sea swell."""
    cx, cy = x + s // 2, y + int(0.42 * s)
    for k, r in enumerate((12, 22, 32, 42)):
        b.arc(cx, cy, r, -0.5 + k * 0.8, 4.4 + k * 0.8, DEEPBLUE, 5)
    b.disc(cx, cy, 7, AMBER)
    # rain, diagonal streaks
    for k in range(4):
        xx = x + int(0.10 * s) + k * int(0.20 * s)
        b.segment(xx, y + int(0.76 * s), xx - 8, y + int(0.92 * s),
                  SKYBLUE, 3)
    # swell
    b.arc(x + int(0.50 * s), y + int(1.02 * s), int(0.30 * s),
          math.pi * 1.15, math.pi * 1.85, DEEPBLUE, 4)


# -------------------------------------------------------------------- layout
STORIES = [
    dict(tag="SHENZHEN", colour=DEEPBLUE,
         head="TRUMP, XI, PUTIN\nMEET IN SHENZHEN",
         body="NUCLEAR ARMS AND IRAN\nTOP THE APEC AGENDA\nIN SHENZHEN TODAY",
         pic=draw_summit),
    dict(tag="THE GULF", colour=CRIMSON,
         head="US AND IRAN TRADE\nFIRE IN THE GULF",
         body="IRAN HITS BASES IN\nKUWAIT AND BAHRAIN;\nUS STRUCK QESHM SITE",
         pic=draw_gulf),
    dict(tag="MARKETS", colour=FOREST,
         head="NVIDIA DOUBLES\nSALES TO $115.8BN",
         body="FIRST RESULTS SINCE\nHUANG OUSTER; H-SERIES\nCHIP SALES TO CHINA HALT",
         pic=draw_chip),
    dict(tag="SPACE", colour=(52, 44, 96),
         head="VOYAGER 1 REACHES\nONE LIGHT-DAY OUT",
         body="48 YEARS ON, THE PROBE\nIS A LIGHT-DAY FROM\nEARTH, NASA CONFIRMS",
         pic=draw_probe),
    dict(tag="EUROPE", colour=(20, 70, 140),
         head="EU PLANS 45BN EURO\nLOAN FOR UKRAINE",
         body="KYIV GETS 45BN EUROS;\nREPAYMENT ONLY AFTER\nRUSSIA PAYS UP",
         pic=draw_euro),
    dict(tag="INDIA", colour=(18, 96, 130),
         head="CYCLONE AKVAN\nNEARS INDIA COAST",
         body="STORM SET TO CROSS\nBETWEEN MACHILIPATNAM\nAND PURI, OFFICIALS SAY",
         pic=draw_storm),
]


def compose():
    b = Board(PAGE_W, PAGE_H, PAPER)
    # outer frame
    b.fill(0, 0, PAGE_W, 6, INK)
    b.fill(0, PAGE_H - 6, PAGE_W, 6, INK)
    b.fill(0, 0, 6, PAGE_H, INK)
    b.fill(PAGE_W - 6, 0, 6, PAGE_H, INK)

    # ---- masthead
    b.draw_centred(24, "THE WORLD TODAY", 9, INK)
    b.rule_h(24, 100, 976, CRIMSON, 6)
    b.draw_centred(118, "THURSDAY, 19 NOVEMBER 2026", 4, CRIMSON)
    b.rule_h(24, 156, 976, INK, 3)

    # ---- lead story: GTA VI
    lx, ly, lw, lh = 24, 172, 976, 212
    b.fill(lx, ly, lw, lh, CARD)
    b.fill(lx, ly, lw, 32, CRIMSON)
    b.draw_text(lx + 16, ly + 6, "LEAD STORY - GAMING", 3, CARD)
    b.draw_text(lx + 20, ly + 48, "GTA VI IS HERE", 5, INK)
    b.draw_text(lx + 20, ly + 90, "VICE CITY OPENS", 5, INK)
    lead = ("AFTER A 13-YEAR WAIT, ROCKSTAR'S BLOCKBUSTER "
            "BEGINS ITS GLOBAL ROLLOUT TODAY AS GAMERS "
            "FLOOD BACK TO VICE CITY")
    for i, line in enumerate(fit_lines(lead, 2, 620)):
        b.draw_text(lx + 20, ly + 142 + i * 17, line, 2, SOFTGREY)
    draw_gta(b, lx + 716, ly + 36, 180)
    b.frame(lx, ly, lw, lh, INK, 3)

    # ---- six story cards, 2 columns x 3 rows
    pw, ph = 482, 170
    for idx, story in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        px = 24 + col * (pw + 12)
        py = 396 + row * (ph + 8)
        b.fill(px, py, pw, ph, CARD)
        b.fill(px, py, pw, 30, story["colour"])
        b.draw_text(px + 12, py + 6, story["tag"], 2, CARD)
        for i, line in enumerate(story["head"].split("\n")):
            b.draw_text(px + 14, py + 40 + i * 26, line, 3, INK)
        for i, line in enumerate(story["body"].split("\n")[:3]):
            b.draw_text(px + 14, py + 100 + i * 17, line, 2, SOFTGREY)
        story["pic"](b, px + pw - 126, py + 38, 112)
        b.frame(px, py, pw, ph, INK, 2)

    # ---- footer ticker
    fy = 934
    b.fill(24, fy, 976, 64, DEEPBLUE)
    b.draw_centred(fy + 10,
                   "ALSO TODAY: FED SEES MORE RATE HIKES - JEFFRIES TO BE FIRST BLACK SPEAKER",
                   2, CARD)
    b.draw_centred(fy + 36,
                   "SOURCES: AP - REUTERS - AFP - BBC - DUCKETT 133 - AUS SANCTIONS SETTLERS",
                   2, (196, 204, 218))
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
