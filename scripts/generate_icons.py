#!/usr/bin/env python3
"""Рисует иконки PWA без внешних библиотек."""

import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "icons"

BG = (11, 18, 32, 255)
CARD = (248, 250, 252, 255)
FOLD = (147, 197, 253, 255)
FOLD_FACE = (219, 234, 254, 255)
LINE = (37, 99, 235, 255)
LINE_SOFT = (148, 163, 184, 255)


def blend(dst, src):
    sr, sg, sb, sa = src
    if sa <= 0:
        return dst
    if sa >= 255:
        return src
    dr, dg, db, da = dst
    a = sa / 255
    out_a = sa + da * (1 - a)
    if out_a <= 0:
        return (0, 0, 0, 0)

    def channel(s, d):
        return round((s * sa + d * da * (1 - a)) / out_a)

    return (channel(sr, dr), channel(sg, dg), channel(sb, db), round(out_a))


def sd_round_box(px, py, cx, cy, half_w, half_h, radius):
    qx = abs(px - cx) - half_w + radius
    qy = abs(py - cy) - half_h + radius
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - radius


def cover(distance):
    return max(0.0, min(1.0, 0.5 - distance))


def paint(size, padding_ratio):
    pixels = [[BG for _ in range(size)] for _ in range(size)]
    margin = size * padding_ratio
    left = margin
    top = size * (0.18 if padding_ratio < 0.2 else 0.22)
    right = size - margin
    bottom = size - top
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    half_w = (right - left) / 2
    half_h = (bottom - top) / 2
    radius = size * 0.08
    fold = (right - left) * 0.22

    for y in range(size):
        for x in range(size):
            px = x + 0.5
            py = y + 0.5
            card = cover(sd_round_box(px, py, cx, cy, half_w, half_h, radius))
            if card <= 0:
                continue

            color = CARD
            in_fold_box = px >= right - fold and py <= top + fold
            if in_fold_box:
                along = (px - (right - fold)) / fold + (py - top) / fold
                if along >= 1:
                    # Срезанный угол листа.
                    color = BG
                    card = 0
                elif along >= 0.82:
                    color = FOLD
                else:
                    # Клапан загнутого угла.
                    flap = (px - (right - fold)) / fold
                    rise = (py - top) / fold
                    if flap + rise >= 0.55 and rise < 0.72 and flap < 0.72:
                        color = FOLD_FACE

            if card > 0:
                src = (*color[:3], round(255 * card))
                pixels[y][x] = blend(pixels[y][x], src)

    def bar(x0, x1, y, thickness, color):
        for y_off in range(thickness):
            yy = y + y_off
            if not (0 <= yy < size):
                continue
            for xx in range(x0, x1):
                if 0 <= xx < size:
                    pixels[yy][xx] = blend(pixels[yy][xx], color)

    inner_left = round(left + (right - left) * 0.16)
    text_top = round(top + (bottom - top) * 0.34)
    gap = max(4, round(size * 0.055))
    thickness = max(2, round(size * 0.028))
    widths = (0.72, 0.56, 0.62, 0.40)
    colors = (LINE, LINE_SOFT, LINE_SOFT, LINE_SOFT)
    for index, (width, color) in enumerate(zip(widths, colors)):
        bar(
            inner_left,
            inner_left + round((right - left) * width),
            text_top + index * gap,
            thickness,
            color,
        )

    return pixels


def write_png(path, pixels):
    height = len(pixels)
    width = len(pixels[0])

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in pixels)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)
    return png


def write_ico(path, png_bytes, size):
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", size if size < 256 else 0, size if size < 256 else 0, 0, 0, 1, 32, len(png_bytes), 22)
    path.write_bytes(header + entry + png_bytes)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = {
        "favicon-32x32.png": 32,
        "favicon-48x48.png": 48,
        "favicon-64x64.png": 64,
        "favicon-128x128.png": 128,
        "favicon-192x192.png": 192,
        "favicon-256x256.png": 256,
        "favicon-512x512.png": 512,
        "apple-touch-icon.png": 180,
    }
    png_32 = None
    for name, size in sizes.items():
        png = write_png(OUT / name, paint(size, 0.14))
        if size == 32:
            png_32 = png
    write_png(OUT / "icon-512-maskable.png", paint(512, 0.28))
    write_ico(OUT / "favicon.ico", png_32, 32)
    print(f"icons written to {OUT}")


if __name__ == "__main__":
    main()
