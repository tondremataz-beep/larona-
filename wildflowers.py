#!/usr/bin/env python3
"""Wildflowers: an animated bouquet for your terminal.

No dependencies, Python 3.8+. Works in any terminal with 256-colour support.

    python3 wildflowers.py --to "Sam" --message "you are my favourite"

Press Ctrl+C to quit.
"""
import argparse
import math
import os
import random
import shutil
import sys
import time

# 256-colour palette indexes
PETALS = [204, 211, 217, 220, 227, 214, 75, 111, 141, 147, 183, 255, 203]
CENTRES = [220, 227, 255, 214]
STEMS = [28, 34, 70, 64]
SPARKLE_COLOURS = [231, 226, 117]
HEART_COLOURS = [197, 204, 211]
MESSAGE_COLOUR = 213


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease(x):
    """Smoothstep: slow start, slow finish."""
    x = clamp(x)
    return x * x * (3 - 2 * x)


class Flower:
    def __init__(self, rng, i, n):
        spread = 1.1  # radians either side of vertical
        frac = i / (n - 1) if n > 1 else 0.5
        self.angle = (frac - 0.5) * 2 * spread + rng.uniform(-0.08, 0.08)
        self.length = rng.uniform(0.55, 1.0)  # fraction of the available height
        self.petal_colour = rng.choice(PETALS)
        self.centre_colour = rng.choice(CENTRES)
        self.stem_colour = rng.choice(STEMS)
        self.radius = rng.uniform(1.6, 3.0)
        self.petals = rng.choice([5, 6, 7, 8])
        self.glyph = rng.choice("@Oo*")
        self.start = rng.uniform(0.2, 3.5)  # seconds before this stem starts growing
        self.phase = rng.uniform(0, math.tau)
        self.spin = rng.choice([-1, 1]) * rng.uniform(0.5, 1.2)


class Scene:
    def __init__(self, width, height, n_flowers, seed):
        rng = random.Random(seed)
        self.w, self.h = width, height
        self.ox = width // 2
        self.oy = height - 5
        self.stem_len = max(6, self.oy - 2)
        spread_x = self.stem_len * math.sin(1.1) + 3
        self.xscale = min(2.0, (width / 2 - 4) / spread_x)
        self.flowers = [Flower(rng, i, n_flowers) for i in range(n_flowers)]
        self.flowers.sort(key=lambda f: abs(f.angle), reverse=True)  # centre drawn last
        self.sparkles = [
            (rng.randrange(width), rng.randrange(max(1, self.oy)),
             rng.uniform(0, math.tau), rng.choice(SPARKLE_COLOURS))
            for _ in range(max(10, width * height // 55))
        ]
        self.hearts = [
            (rng.uniform(0, 8), rng.uniform(-self.xscale * 8, self.xscale * 8),
             rng.uniform(0, math.tau), rng.choice(HEART_COLOURS))
            for _ in range(8)
        ]

    def draw(self, t, message):
        buf = {}

        def put(x, y, ch, colour):
            x, y = int(round(x)), int(round(y))
            if 0 <= x < self.w and 0 <= y < self.h:
                buf[(x, y)] = (ch, colour)

        # sparkles in the background
        for x, y, ph, colour in self.sparkles:
            v = math.sin(t * 1.7 + ph)
            if v > 0.6:
                put(x, y, "+" if v > 0.9 else ".", colour)

        for f in self.flowers:
            grow = ease((t - f.start * 0.6) / 1.6)
            if grow <= 0:
                continue
            a = f.angle + 0.05 * math.sin(t * 1.1 + f.phase) * grow
            length = f.length * self.stem_len * grow
            steps = int(length * 2) + 1
            ch = "|" if abs(a) < 0.3 else ("/" if a > 0 else "\\")
            for s in range(steps + 1):
                u = s / steps
                x = self.ox + math.sin(a) * length * u * self.xscale
                y = self.oy - math.cos(a) * length * u
                put(x, y, ch, STEMS[(s // 4 + STEMS.index(f.stem_colour)) % len(STEMS)])

            tx = self.ox + math.sin(a) * length * self.xscale
            ty = self.oy - math.cos(a) * length
            if grow < 0.99:
                continue
            bloom = ease((t - f.start - 1.2) / 2.2)
            if bloom < 0.15:
                put(tx, ty, "o", f.petal_colour)  # bud
                continue
            r = f.radius * bloom * (1 + 0.08 * math.sin(t * 2 + f.phase))
            rot = t * 0.25 * f.spin
            n = f.petals
            for k in range(n):
                ang = rot + math.tau * k / n
                put(tx + math.cos(ang) * r * 2, ty + math.sin(ang) * r * 0.85, f.glyph, f.petal_colour)
            if r > 1.4:
                for k in range(n):
                    ang = rot + math.pi / n + math.tau * k / n
                    put(tx + math.cos(ang) * r, ty + math.sin(ang) * r * 0.45, "o", f.petal_colour)
            put(tx, ty, "@", f.centre_colour)

        # ribbon around the stems
        for i, c in enumerate("\\~{@}~/"):
            put(self.ox - 3 + i, self.oy + 1, c, MESSAGE_COLOUR)

        # hearts drifting up once the bouquet is mostly in bloom
        if t > 3:
            for off, dx, ph, colour in self.hearts:
                age = (t + off) % 8
                y = self.oy - 1 - age * self.oy / 8
                x = self.ox + dx + 2 * math.sin(age * 1.5 + ph)
                put(x, y, "\u2665", colour)

        # message types itself out
        shown = int(max(0.0, t - 6.0) * 14)
        text = message[:shown]
        x0 = self.ox - len(message) // 2
        for i, c in enumerate(text):
            put(x0 + i, self.oy + 3, c, MESSAGE_COLOUR)
        return buf

    def to_lines(self, buf, colour=True):
        lines = []
        for y in range(self.h):
            out, cur = [], None
            for x in range(self.w):
                cell = buf.get((x, y))
                if cell is None:
                    if cur is not None:
                        out.append("\x1b[0m")
                        cur = None
                    out.append(" ")
                else:
                    ch, c = cell
                    if colour and c != cur:
                        out.append(f"\x1b[38;5;{c}m")
                        cur = c
                    out.append(ch)
            if cur is not None:
                out.append("\x1b[0m")
            lines.append("".join(out).rstrip())
        return lines


def terminal_size():
    cols, rows = shutil.get_terminal_size(fallback=(100, 32))
    return max(40, cols), max(14, rows - 1)  # leave a row so the last line never scrolls


def main():
    ap = argparse.ArgumentParser(description="An animated wildflower bouquet for your terminal.")
    ap.add_argument("--to", default="", help="name to put at the end of the message")
    ap.add_argument("--message", default="you are my forever favourite", help="message under the bouquet")
    ap.add_argument("--flowers", type=int, default=15, help="number of flowers (default 15)")
    ap.add_argument("--fps", type=int, default=24, help="frames per second (default 24)")
    ap.add_argument("--seed", type=int, default=None, help="fixed seed for the same bouquet every time")
    ap.add_argument("--snapshot", type=float, metavar="SECONDS",
                    help="print one frame at this time and exit (no animation)")
    ap.add_argument("--no-color", action="store_true", help="plain text, no colour")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name == "nt":
        os.system("")  # switches on ANSI escape codes in Windows 10+ terminals

    message = args.message + (f", {args.to}" if args.to else "")
    seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    n = max(3, args.flowers)

    w, h = terminal_size()
    scene = Scene(w, h, n, seed)

    if args.snapshot is not None:
        buf = scene.draw(args.snapshot, message)
        print("\n".join(scene.to_lines(buf, colour=not args.no_color)))
        return

    out = sys.stdout
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
    try:
        t0 = time.perf_counter()
        frame_time = 1.0 / max(1, args.fps)
        while True:
            start = time.perf_counter()
            size = terminal_size()
            if size != (scene.w, scene.h):
                w, h = size
                scene = Scene(w, h, n, seed)
                out.write("\x1b[2J")
            buf = scene.draw(start - t0, message)
            out.write("\x1b[H" + "\n".join(scene.to_lines(buf, colour=not args.no_color)))
            out.flush()
            time.sleep(max(0.0, frame_time - (time.perf_counter() - start)))
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()


if __name__ == "__main__":
    main()
