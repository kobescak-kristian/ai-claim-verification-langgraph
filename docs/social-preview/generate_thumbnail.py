#!/usr/bin/env python3
"""
LinkedIn post thumbnail — LangGraph comparison post
(ai-claim-verification-langgraph). 1200x627, design system mirrored
from kobescak-kristian.github.io :root palette — same system as the
2026-07-20 orchestrator post thumbnail.

Fonts (not committed; fetch before running):
  Bricolage Grotesque (variable) + IBM Plex Mono, from
  https://github.com/google/fonts (ofl/bricolagegrotesque, ofl/ibmplexmono)
  into ./fonts/

Every number and label binds to published files:
  parity 1.00/1.00, 35 claims -> evals/parity_run_2026-07-20.md
  509 -> 585 lines, 15%       -> COMPARISON.md / README.md
                                 (re-measured 2026-07-24)
Usage: python generate_thumbnail.py [out.png]
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 627

# --- site palette (kobescak-kristian.github.io :root) ---
DARK      = "#10201A"   # --dark
DARK_2    = "#16291F"   # --dark-2
DARK_INK  = "#DFE9E2"   # --dark-ink
DARK_MUT  = "#8FA79A"   # --dark-muted
DARK_RULE = "#24382E"   # --dark-rule
AMBER     = "#E5B96B"   # site accent
STAMP_BR  = "#0E8563"   # --stamp-bright

FDIR = "fonts/"

def brico(size, wght=800):
    f = ImageFont.truetype(FDIR + "BricolageGrotesque.ttf", size)
    try:
        f.set_variation_by_axes([14, 100, wght])  # opsz, wdth, wght
    except Exception:
        pass
    return f

def mono(size, medium=False):
    name = "IBMPlexMono-Medium.ttf" if medium else "IBMPlexMono-Regular.ttf"
    return ImageFont.truetype(FDIR + name, size)

img = Image.new("RGB", (W, H), DARK)
d = ImageDraw.Draw(img)

# subtle grid (56px cells, low opacity)
grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for x in range(0, W, 56):
    gd.line([(x, 0), (x, H)], fill=DARK_RULE, width=1)
for y in range(0, H, 56):
    gd.line([(0, y), (W, y)], fill=DARK_RULE, width=1)
grid.putalpha(grid.split()[3].point(lambda a: int(a * 0.45)))
img = Image.alpha_composite(img.convert("RGBA"), grid)
d = ImageDraw.Draw(img)

M = 84  # left margin

# --- stamp label (mono, letterspaced, bordered, slight rotation) ---
label = "O N E   S Y S T E M   ·   T W O   B U I L D S   ·   O N E   F R O Z E N   E X A M"
lf = mono(19, medium=True)
lw = d.textlength(label, font=lf)
pad_x, pad_y = 18, 12
stamp = Image.new("RGBA", (int(lw) + 2 * pad_x + 6, 19 + 2 * pad_y + 8), (0, 0, 0, 0))
sd = ImageDraw.Draw(stamp)
sd.rounded_rectangle(
    [0, 0, stamp.width - 3, stamp.height - 3],
    radius=6, outline=AMBER, width=2)
sd.text((pad_x, pad_y - 2), label, font=lf, fill=AMBER)
stamp = stamp.rotate(1.5, expand=True, resample=Image.BICUBIC)
img.alpha_composite(stamp, (M, 74))
d = ImageDraw.Draw(img)

# --- headline (Bricolage 800) ---
h1a = "The framework made"
h1b = "my agent 15% bigger."
hf = brico(88, 800)
d.text((M, 188), h1a, font=hf, fill=DARK_INK)
d.text((M, 288), h1b, font=hf, fill=DARK_INK)

# thin amber underline under "15% bigger" (site .u highlight gesture)
pre = d.textlength("my agent ", font=hf)
seg = d.textlength("15% bigger", font=hf)
d.rectangle([M + pre, 288 + 96, M + pre + seg, 288 + 102], fill=AMBER)

# --- evidence lines (mono, bind to published files) ---
d.text((M, 442), "same frozen gate  P 1.00 · R 1.00   |   35/35 claims · synthetic dataset",
       font=mono(22), fill=DARK_MUT)
d.text((M, 478), "agent layer 509 -> 585 lines · enforcement relocated, not removed",
       font=mono(22), fill=DARK_MUT)

# --- footer rule + repo path with brand dot ---
d.line([(M, 524), (W - M, 524)], fill=DARK_RULE, width=2)
d.rounded_rectangle([M, 552, M + 16, 568], radius=4, fill=STAMP_BR)
d.text((M + 30, 548), "github.com/kobescak-kristian/ai-claim-verification-langgraph",
       font=mono(23, medium=True), fill=DARK_INK)

out = sys.argv[1] if len(sys.argv) > 1 else "langgraph-comparison-post-thumb.png"
img.convert("RGB").save(out, "PNG")
print(f"written {out} ({W}x{H})")
