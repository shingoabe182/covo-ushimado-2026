"""COVO USHIMADO website renewal mockup generator.

Renders a high-fidelity luxury website mockup as PNG files using PIL.
Aesthetic reference: sankara hotel & spa / snow peak field suite spa / soki atami.
Tone target: minimal, serene, warm luxury — Setouchi inland sea inspired.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
import math
import random

random.seed(42)

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# COLOR PALETTE — Setouchi warm luxury
# ============================================================
INK       = (31, 27, 23)      # deep warm charcoal — primary text
INK_SOFT  = (74, 66, 58)      # secondary text
MUTED     = (138, 128, 116)   # tertiary text / captions
CREAM     = (250, 246, 236)   # primary background
SAND      = (235, 226, 210)   # secondary background
SAND_DEEP = (216, 202, 178)
SUNSET    = (182, 133, 106)   # muted terracotta accent
SEA       = (79, 100, 105)    # deep sea green-gray
SEA_SOFT  = (167, 184, 184)   # surface sea
OLIVE     = (138, 145, 118)
SUMI      = (24, 22, 20)      # for very dark areas
WHITE     = (255, 254, 250)

# Fonts available in sandbox
FONT_JP   = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
FONT_SERIF= "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
FONT_SERIF_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
FONT_SERIF_B  = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ff(path, size):
    return ImageFont.truetype(path, size)


# ============================================================
# Mixed Latin/JP text rendering
# Droid Sans Fallback doesn't carry latin glyphs in this sandbox,
# so we segment the string and switch fonts per character class.
# ============================================================
def _is_cjk(ch):
    cp = ord(ch)
    return (
        0x3000 <= cp <= 0x303F or   # CJK punctuation
        0x3040 <= cp <= 0x309F or   # Hiragana
        0x30A0 <= cp <= 0x30FF or   # Katakana
        0x4E00 <= cp <= 0x9FFF or   # CJK unified
        0xFF00 <= cp <= 0xFFEF      # Fullwidth
    )


def _segment(text):
    """Split into runs: ('jp', '海') / ('lt', 'covo')."""
    runs = []
    cur = ""
    cur_kind = None
    for ch in text:
        k = "jp" if _is_cjk(ch) else "lt"
        if k != cur_kind and cur:
            runs.append((cur_kind, cur))
            cur = ""
        cur += ch
        cur_kind = k
    if cur:
        runs.append((cur_kind, cur))
    return runs


def measure_mixed(text, font_lt, font_jp, letter_spacing=0):
    """Return pixel width of mixed-script line."""
    runs = _segment(text)
    total = 0
    for kind, seg in runs:
        f = font_jp if kind == "jp" else font_lt
        if letter_spacing:
            total += sum(f.getlength(c) + letter_spacing for c in seg) - letter_spacing
            total += letter_spacing  # gap before next run
        else:
            total += f.getlength(seg)
    if letter_spacing:
        total -= letter_spacing  # trailing
    return total


def text_mixed(draw, xy, text, font_lt, font_jp, fill, anchor="lm",
               letter_spacing=0, baseline_shift_jp=0):
    """Draw text with separate Latin / Japanese fonts.

    anchor: lm = left-middle, mm = center-middle, rm = right-middle
    baseline_shift_jp: extra y offset for JP glyphs (positive = down).
    """
    width = measure_mixed(text, font_lt, font_jp, letter_spacing)
    x, y = xy
    if anchor[0] == "m":
        x -= width / 2
    elif anchor[0] == "r":
        x -= width

    runs = _segment(text)
    for kind, seg in runs:
        f = font_jp if kind == "jp" else font_lt
        yy = y + (baseline_shift_jp if kind == "jp" else 0)
        if letter_spacing:
            for c in seg:
                draw.text((x, yy), c, font=f, fill=fill, anchor="lm")
                x += f.getlength(c) + letter_spacing
            x -= letter_spacing
            x += letter_spacing  # gap before next run
        else:
            draw.text((x, yy), seg, font=f, fill=fill, anchor="lm")
            x += f.getlength(seg)


# ============================================================
# Helpers
# ============================================================
def fill_vertical_gradient(img, box, c1, c2):
    """Fill rectangle with vertical gradient from c1 (top) to c2 (bottom)."""
    x0, y0, x1, y1 = box
    h = y1 - y0
    if h <= 0:
        return
    grad = Image.new("RGB", (1, h), c1)
    px = grad.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        px[0, y] = (r, g, b)
    grad = grad.resize((x1 - x0, h))
    img.paste(grad, (x0, y0))


def fill_radial(img, cx, cy, radius, color_inner, color_outer):
    """Subtle radial highlight."""
    size = radius * 2
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 60
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(t * radius)
        a = int((1 - t) * 90)
        col = (
            int(color_inner[0] * (1 - t) + color_outer[0] * t),
            int(color_inner[1] * (1 - t) + color_outer[1] * t),
            int(color_inner[2] * (1 - t) + color_outer[2] * t),
            a,
        )
        d.ellipse([radius - r, radius - r, radius + r, radius + r], fill=col)
    img.paste(layer, (cx - radius, cy - radius), layer)


def add_grain(img, amount=6):
    """Add subtle film grain for luxury feel."""
    w, h = img.size
    noise = Image.new("L", (w, h))
    px = noise.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = 128 + random.randint(-amount, amount)
    noise = noise.filter(ImageFilter.GaussianBlur(0.4))
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    out = Image.blend(img.convert("RGB"), noise_rgb, 0.04)
    return out


def text_centered(draw, xy, text, font, fill, anchor="mm", spacing=0, line_height=None):
    """Draw text centered or anchored."""
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def draw_thin_line(draw, p1, p2, color, width=1):
    draw.line([p1, p2], fill=color, width=width)


def draw_letterspaced(draw, xy, text, font, fill, spacing_px=2, anchor="lm"):
    """Manual letter-spacing for chic small caps."""
    x, y = xy
    total = sum(font.getlength(c) + spacing_px for c in text) - spacing_px
    if anchor == "mm":
        x -= total / 2
    elif anchor == "rm":
        x -= total
    for c in text:
        draw.text((x, y), c, font=font, fill=fill, anchor="lm")
        x += font.getlength(c) + spacing_px


def wrap_jp(text, max_per_line):
    """Naive wrap for Japanese — by char count."""
    lines = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
        else:
            cur += ch
            if len(cur) >= max_per_line:
                lines.append(cur)
                cur = ""
    if cur:
        lines.append(cur)
    return lines


# ============================================================
# Image placeholder generators (suggest the real photography)
# ============================================================
def make_sea_horizon(w, h, sky_top=(238, 226, 208), sky_bot=(212, 195, 175),
                    sea_top=(150, 168, 168), sea_bot=(98, 122, 126), horizon_at=0.55):
    """Sea + sky placeholder evoking Setouchi sunset."""
    img = Image.new("RGB", (w, h), sky_top)
    fill_vertical_gradient(img, (0, 0, w, int(h * horizon_at)), sky_top, sky_bot)
    fill_vertical_gradient(img, (0, int(h * horizon_at), w, h), sea_top, sea_bot)
    # subtle sun glow
    sun_y = int(h * (horizon_at - 0.12))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(220, 20, -10):
        a = max(0, int(60 * (1 - r / 220)))
        gd.ellipse([w // 2 - r, sun_y - r, w // 2 + r, sun_y + r],
                   fill=(255, 220, 190, a))
    img.paste(glow, (0, 0), glow)
    # horizon line glimmer (very subtle)
    d = ImageDraw.Draw(img)
    glim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glim)
    gd.line([(0, int(h * horizon_at)), (w, int(h * horizon_at))],
            fill=(255, 240, 220, 140), width=1)
    glim = glim.filter(ImageFilter.GaussianBlur(0.6))
    img.paste(glim, (0, 0), glim)
    # very faint, blurred water shimmer (no hard lines)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    horizon_y = int(h * horizon_at)
    for i in range(20):
        ry = horizon_y + random.randint(8, h - horizon_y - 4)
        sd.line([(random.randint(0, w // 4), ry),
                 (random.randint(int(w * 0.75), w), ry)],
                fill=(255, 245, 220, 18), width=1)
    sh = sh.filter(ImageFilter.GaussianBlur(2.5))
    img.paste(sh, (0, 0), sh)
    return img


def make_villa_dusk(w, h):
    """Dusk villa silhouette: sky + warm window light hints."""
    img = Image.new("RGB", (w, h), (40, 48, 56))
    fill_vertical_gradient(img, (0, 0, w, int(h * 0.55)),
                           (212, 168, 140), (114, 110, 118))
    fill_vertical_gradient(img, (0, int(h * 0.55), w, h),
                           (88, 92, 96), (38, 40, 44))
    d = ImageDraw.Draw(img)
    # silhouette villa
    base_y = int(h * 0.78)
    villa_w = int(w * 0.45)
    vx = int(w * 0.27)
    # roof
    d.polygon([(vx, base_y), (vx + villa_w // 2, int(base_y - h * 0.16)),
               (vx + villa_w, base_y)], fill=(28, 28, 30))
    # body
    d.rectangle([vx, base_y, vx + villa_w, int(h * 0.93)], fill=(34, 34, 36))
    # warm window
    win_w = int(villa_w * 0.42)
    win_h = int(h * 0.07)
    wx = vx + int((villa_w - win_w) / 2)
    wy = base_y + int(h * 0.03)
    d.rectangle([wx, wy, wx + win_w, wy + win_h], fill=(255, 198, 130))
    # window soft glow
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rectangle([wx - 14, wy - 14, wx + win_w + 14, wy + win_h + 14],
                 fill=(255, 198, 130, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    img.paste(glow, (0, 0), glow)
    # ground line
    d.rectangle([0, int(h * 0.93), w, h], fill=(22, 20, 22))
    return img


def make_sauna(w, h):
    """Warm wood interior with steam."""
    img = Image.new("RGB", (w, h), (74, 50, 36))
    fill_vertical_gradient(img, (0, 0, w, h), (118, 80, 54), (52, 34, 22))
    d = ImageDraw.Draw(img)
    # natural irregular wood planks
    x = 0
    while x < w:
        plank_w = random.randint(58, 92)
        # plank tone variation
        tone = random.randint(-22, 18)
        col = (max(0, 110 + tone), max(0, 74 + tone), max(0, 50 + tone))
        d.rectangle([x, 0, x + plank_w, h], fill=col)
        # darker seam on right of plank
        d.line([(x + plank_w - 1, 0), (x + plank_w - 1, h)],
               fill=(30, 20, 12), width=1)
        # wood grain — faint horizontal streaks
        grain = Image.new("RGBA", (plank_w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grain)
        for _ in range(random.randint(2, 5)):
            gy = random.randint(0, h)
            gd.line([(2, gy), (plank_w - 3, gy + random.randint(-6, 6))],
                    fill=(40, 26, 16, 50), width=1)
        # small knots
        if random.random() < 0.18:
            ky = random.randint(20, h - 20)
            kr = random.randint(4, 8)
            gd.ellipse([plank_w // 2 - kr, ky - kr, plank_w // 2 + kr, ky + kr],
                       fill=(40, 24, 14, 110))
        grain = grain.filter(ImageFilter.GaussianBlur(1.2))
        img.paste(grain, (x, 0), grain)
        x += plank_w
    # global wood color overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, w, h], fill=(30, 18, 10, 30))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    # warm light blob from upper right (window)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([int(w * 0.45), int(h * -0.1), int(w * 1.05), int(h * 0.75)],
               fill=(255, 196, 130, 110))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)
    # bench silhouette (bottom)
    d2 = ImageDraw.Draw(img)
    d2.rectangle([0, int(h * 0.78), w, int(h * 0.84)], fill=(58, 38, 24))
    d2.rectangle([0, int(h * 0.84), w, h], fill=(38, 24, 16))
    # steam softness
    steam = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(steam)
    for _ in range(28):
        cx = random.randint(0, w)
        cy = random.randint(0, int(h * 0.75))
        rr = random.randint(30, 110)
        sd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   fill=(255, 240, 220, 22))
    steam = steam.filter(ImageFilter.GaussianBlur(40))
    img.paste(steam, (0, 0), steam)
    return img


def make_dining(w, h):
    """Plate-on-linen feeling — warm tabletop."""
    img = Image.new("RGB", (w, h), (220, 200, 174))
    fill_vertical_gradient(img, (0, 0, w, h), (228, 212, 188), (190, 168, 138))
    d = ImageDraw.Draw(img)
    # plate
    cx, cy = w // 2, h // 2
    pr = int(min(w, h) * 0.32)
    d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=(248, 240, 224),
              outline=(214, 200, 180), width=2)
    d.ellipse([cx - pr + 18, cy - pr + 18, cx + pr - 18, cy + pr - 18],
              outline=(232, 218, 198), width=1)
    # subtle food blob
    fr = int(pr * 0.45)
    d.ellipse([cx - fr, cy - fr, cx + fr, cy + fr], fill=(180, 132, 92))
    d.ellipse([cx - fr + 6, cy - fr + 4, cx + fr - 6, cy + fr - 4], fill=(150, 100, 64))
    # vignette
    vig = Image.new("RGBA", img.size, (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    vd.rectangle([0, 0, w, h], fill=(60, 40, 30, 50))
    vd.ellipse([-w // 2, -h // 2, w + w // 2, h + h // 2], fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    return img


def make_olive_field(w, h):
    """Olive grove feeling — for Ushimado (olive island region)."""
    img = Image.new("RGB", (w, h), (210, 218, 184))
    fill_vertical_gradient(img, (0, 0, w, h), (226, 226, 198), (146, 158, 122))
    d = ImageDraw.Draw(img)
    # rolling silhouettes
    d.ellipse([-w // 4, int(h * 0.55), w // 2, int(h * 1.5)], fill=(122, 138, 102))
    d.ellipse([w // 3, int(h * 0.65), w + w // 4, int(h * 1.6)], fill=(102, 120, 88))
    # leafy hint — clusters
    for _ in range(80):
        cx = random.randint(0, w)
        cy = random.randint(int(h * 0.4), h)
        rr = random.randint(8, 20)
        c = random.choice([(118, 138, 96), (140, 156, 112), (96, 116, 80)])
        d.ellipse([cx - rr, cy - rr // 2, cx + rr, cy + rr // 2], fill=c)
    return img


def make_interior_morning(w, h):
    """Bright villa interior — large window with ocean light, furniture."""
    img = Image.new("RGB", (w, h), (242, 232, 216))
    fill_vertical_gradient(img, (0, 0, w, h), (250, 240, 222), (208, 192, 170))
    d = ImageDraw.Draw(img)
    # back wall
    d.rectangle([0, 0, w, int(h * 0.84)], fill=(240, 228, 210))
    # window frame
    win_x = int(w * 0.14)
    win_w = int(w * 0.72)
    win_y = int(h * 0.10)
    win_h = int(h * 0.62)
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], fill=(196, 212, 214))
    # gradient sea/sky inside window
    fill_vertical_gradient(img, (win_x, win_y, win_x + win_w, win_y + int(win_h * 0.55)),
                           (242, 230, 214), (208, 210, 198))
    fill_vertical_gradient(img, (win_x, win_y + int(win_h * 0.55), win_x + win_w, win_y + win_h),
                           (148, 168, 168), (88, 110, 116))
    # horizon glimmer
    d.line([(win_x, win_y + int(win_h * 0.55)), (win_x + win_w, win_y + int(win_h * 0.55))],
           fill=(248, 232, 210), width=1)
    # window frame — slim
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h],
                outline=(72, 60, 48), width=3)
    # vertical mullions (3 sections)
    third = win_w // 3
    d.line([(win_x + third, win_y), (win_x + third, win_y + win_h)],
           fill=(72, 60, 48), width=2)
    d.line([(win_x + third * 2, win_y), (win_x + third * 2, win_y + win_h)],
           fill=(72, 60, 48), width=2)
    # floor (wood plank)
    floor_y = int(h * 0.78)
    d.rectangle([0, floor_y, w, h], fill=(168, 142, 110))
    for px in range(0, w, w // 12):
        d.line([(px, floor_y), (px, h)], fill=(140, 116, 88), width=1)
    # subtle floor gradient (light falls from window)
    floor_light = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fld = ImageDraw.Draw(floor_light)
    fld.polygon([(win_x + 20, floor_y + 4),
                  (win_x + win_w - 20, floor_y + 4),
                  (w * 0.92, h),
                  (w * 0.08, h)],
                 fill=(255, 235, 200, 60))
    floor_light = floor_light.filter(ImageFilter.GaussianBlur(8))
    img.paste(floor_light, (0, 0), floor_light)
    d = ImageDraw.Draw(img)

    # sofa / bench (low silhouette)
    sf_x = int(w * 0.18)
    sf_w = int(w * 0.64)
    sf_y = int(h * 0.62)
    sf_h = int(h * 0.18)
    d.rectangle([sf_x, sf_y, sf_x + sf_w, sf_y + sf_h], fill=(196, 178, 152))
    d.rectangle([sf_x, sf_y, sf_x + sf_w, sf_y + 14], fill=(210, 192, 168))
    # legs
    d.rectangle([sf_x + 8, sf_y + sf_h, sf_x + 18, sf_y + sf_h + 8], fill=(60, 48, 36))
    d.rectangle([sf_x + sf_w - 18, sf_y + sf_h, sf_x + sf_w - 8, sf_y + sf_h + 8], fill=(60, 48, 36))
    # cushion
    d.rounded_rectangle([sf_x + 26, sf_y - 18, sf_x + 100, sf_y + 8],
                        radius=6, fill=(176, 144, 116))
    # small side table + lamp left of sofa
    tx = int(w * 0.07)
    ty = int(h * 0.68)
    d.rectangle([tx, ty, tx + 50, ty + 60], fill=(122, 96, 70))
    d.rectangle([tx + 12, ty - 32, tx + 38, ty], fill=(212, 188, 156))  # lamp shade
    d.line([(tx + 25, ty), (tx + 25, ty + 60)], fill=(80, 60, 40), width=1)
    return img


# ============================================================
# Section drawing functions
# ============================================================
W = 1440  # desktop width


def section_hero(h=820):
    img = make_sea_horizon(W, h, sky_top=(238, 224, 208), sky_bot=(206, 196, 184),
                           sea_top=(162, 176, 174), sea_bot=(94, 112, 116),
                           horizon_at=0.6)
    d = ImageDraw.Draw(img)

    # Top nav — translucent overlay
    nav = Image.new("RGBA", (W, 90), (250, 246, 236, 0))
    d.rectangle([0, 0, W, 90], fill=None)
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(nav, (0, 0))
    img = img_rgba.convert("RGB")
    d = ImageDraw.Draw(img)

    # Logo "covo" — small serif top-left
    f_logo = ff(FONT_SERIF, 30)
    d.text((68, 45), "c o v o", font=f_logo, fill=WHITE, anchor="lm")

    # Nav items right
    f_nav = ff(FONT_SERIF, 13)
    nav_items = ["STAY", "SAUNA", "DINING", "EXPERIENCE", "ACCESS", "NEWS"]
    nx = W - 240
    for item in nav_items:
        draw_letterspaced(d, (nx, 45), item, f_nav, WHITE, spacing_px=2, anchor="mm")
        nx -= 110
    # JP / EN switch
    f_lang = ff(FONT_SERIF, 12)
    d.text((W - 68, 45), "JP / EN", font=f_lang, fill=(255, 255, 255, 200), anchor="rm")

    # Reservation button (top-right capsule)
    btn_w, btn_h = 150, 38
    btn_x = W - 68 - btn_w
    btn_y = 78
    # Place button below nav line for breathing
    # Hero center text
    cx = W // 2
    cy_top = int(h * 0.42)

    # Eyebrow
    f_eye = ff(FONT_SERIF, 14)
    draw_letterspaced(d, (cx, cy_top - 80), "SETOUCHI . USHIMADO", f_eye, WHITE,
                      spacing_px=4, anchor="mm")
    # thin horizontal line
    d.line([(cx - 28, cy_top - 60), (cx + 28, cy_top - 60)], fill=WHITE, width=1)

    # Big serif headline (EN)
    f_h1 = ff(FONT_SERIF_IT, 84)
    d.text((cx, cy_top + 0), "A quiet escape", font=f_h1, fill=WHITE, anchor="mm")
    d.text((cx, cy_top + 90), "by the inland sea.", font=f_h1, fill=WHITE, anchor="mm")

    # JP tagline
    f_jp = ff(FONT_JP, 22)
    d.text((cx, cy_top + 180), "瀬戸内に、ひっそりと佇む二組だけの隠れ家。",
           font=f_jp, fill=WHITE, anchor="mm")

    # Bottom corner content
    # Scroll indicator
    f_sm = ff(FONT_SERIF, 11)
    draw_letterspaced(d, (80, h - 60), "SCROLL", f_sm, (255, 255, 255, 210),
                      spacing_px=3, anchor="lm")
    d.line([(80, h - 40), (80, h - 12)], fill=WHITE, width=1)

    # Reservation pill, bottom-right
    pill_w = 200
    pill_h = 48
    px0 = W - 68 - pill_w
    py0 = h - 80
    d.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h],
                        radius=24, fill=WHITE)
    f_btn = ff(FONT_SERIF, 14)
    draw_letterspaced(d, (px0 + pill_w // 2, py0 + pill_h // 2 + 1),
                      "RESERVATION", f_btn, INK, spacing_px=3, anchor="mm")

    # Side caption left middle - vertical-ish small text
    f_cap = ff(FONT_SERIF, 11)
    cap = "EST . 2024  /  2 SUITES ONLY"
    draw_letterspaced(d, (80, h // 2), cap, f_cap, (255, 255, 255, 220),
                      spacing_px=3, anchor="lm")

    return img


def section_intro(h=560):
    img = Image.new("RGB", (W, h), CREAM)
    d = ImageDraw.Draw(img)
    cx = W // 2

    # Eyebrow
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (cx, 100), "CONCEPT", f_eye, SUNSET, spacing_px=5, anchor="mm")
    d.line([(cx - 18, 124), (cx + 18, 124)], fill=SUNSET, width=1)

    # Big headline JP
    f_h1 = ff(FONT_JP, 44)
    d.text((cx, 200), "海と、静けさと、わたしだけの時間。", font=f_h1, fill=INK, anchor="mm")

    # English supporting
    f_h2 = ff(FONT_SERIF_IT, 28)
    d.text((cx, 260), "Where the inland sea meets your own quiet hour.",
           font=f_h2, fill=INK_SOFT, anchor="mm")

    # Body — Japanese paragraphs centered
    f_body = ff(FONT_JP, 16)
    body_lines = [
        "日々の喧騒からそっと離れ、",
        "瀬戸内の海をひとり占めする一棟貸しのヴィラ。",
        "潮の香りに包まれ、薪のはぜる音を聴き、",
        "湯と食と、ただ流れる時間を、心ゆくまで。",
    ]
    y = 330
    for line in body_lines:
        d.text((cx, y), line, font=f_body, fill=INK_SOFT, anchor="mm")
        y += 36

    # Bottom small horizontal line
    d.line([(cx - 40, h - 80), (cx + 40, h - 80)], fill=SAND_DEEP, width=1)

    return img


def section_stay(h=820):
    img = Image.new("RGB", (W, h), SAND)
    d = ImageDraw.Draw(img)

    # Eyebrow
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (W // 2, 90), "STAY", f_eye, SUNSET, spacing_px=5, anchor="mm")
    d.line([(W // 2 - 18, 114), (W // 2 + 18, 114)], fill=SUNSET, width=1)

    f_h = ff(FONT_SERIF_IT, 52)
    d.text((W // 2, 178), "Two villas, two stories.", font=f_h, fill=INK, anchor="mm")
    f_jp = ff(FONT_JP, 18)
    f_jp_lt = ff(FONT_SERIF, 18)
    text_mixed(d, (W // 2, 226), "1日2組限定、それぞれに物語のある2棟。",
               f_jp_lt, f_jp, INK_SOFT, anchor="mm")

    # Two villas side by side
    card_w = 520
    card_h = 420
    gap = 60
    total_w = card_w * 2 + gap
    x0 = (W - total_w) // 2
    y0 = 290

    # Card 1 — villa A "anbai" (interior morning)
    img_a = make_interior_morning(card_w, card_h)
    img.paste(img_a, (x0, y0))
    # subtle frame
    d.rectangle([x0, y0, x0 + card_w, y0 + card_h], outline=SAND_DEEP, width=1)
    # caption below image
    f_no = ff(FONT_SERIF_IT, 14)
    d.text((x0, y0 + card_h + 24), "Villa  No.  01", font=f_no, fill=SUNSET, anchor="lm")
    f_name_jp = ff(FONT_JP, 26)
    f_name_lt = ff(FONT_SERIF, 26)
    text_mixed(d, (x0, y0 + card_h + 60), "Anbai — 塩梅",
               f_name_lt, f_name_jp, INK, anchor="lm")
    f_desc_jp = ff(FONT_JP, 13)
    f_desc_lt = ff(FONT_SERIF, 13)
    text_mixed(d, (x0, y0 + card_h + 96),
               "海を望む大窓と、薪ストーブのあるリビング。最大4名様。",
               f_desc_lt, f_desc_jp, INK_SOFT, anchor="lm")

    # Card 2 — villa B "nagi" (sea horizon)
    img_b = make_sea_horizon(card_w, card_h, sky_top=(236, 218, 200), sky_bot=(200, 196, 188),
                              sea_top=(150, 168, 168), sea_bot=(80, 100, 108),
                              horizon_at=0.5)
    img.paste(img_b, (x0 + card_w + gap, y0))
    d.rectangle([x0 + card_w + gap, y0, x0 + card_w * 2 + gap, y0 + card_h],
                outline=SAND_DEEP, width=1)
    d.text((x0 + card_w + gap, y0 + card_h + 24), "Villa  No.  02", font=f_no, fill=SUNSET, anchor="lm")
    text_mixed(d, (x0 + card_w + gap, y0 + card_h + 60), "Nagi — 凪",
               f_name_lt, f_name_jp, INK, anchor="lm")
    text_mixed(d, (x0 + card_w + gap, y0 + card_h + 96),
               "オーシャンビューの専用バスとデッキ。最大4名様。",
               f_desc_lt, f_desc_jp, INK_SOFT, anchor="lm")

    return img


def section_sauna(h=620):
    img = Image.new("RGB", (W, h), SUMI)
    d = ImageDraw.Draw(img)

    # Left half — image, right half — text
    half = W // 2
    sauna_img = make_sauna(half, h)
    img.paste(sauna_img, (0, 0))

    # Right text panel
    tx = half + 100
    # Eyebrow
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (tx, 130), "SAUNA", f_eye, (220, 180, 140), spacing_px=5, anchor="lm")
    d.line([(tx, 152), (tx + 36, 152)], fill=(220, 180, 140), width=1)

    f_h = ff(FONT_SERIF_IT, 46)
    d.text((tx, 220), "Heat. Breath.", font=f_h, fill=WHITE, anchor="lm")
    d.text((tx, 270), "The sea.", font=f_h, fill=WHITE, anchor="lm")

    f_jp = ff(FONT_JP, 18)
    body = [
        "瀬戸内の海を望むフィンランド式バレルサウナ。",
        "薪の香りに包まれて整う、",
        "ここでしか味わえない外気浴。",
    ]
    y = 340
    for line in body:
        d.text((tx, y), line, font=f_jp, fill=(232, 224, 210), anchor="lm")
        y += 34

    # Small caption
    f_cap = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (tx, h - 80), "FINNISH  BARREL  /  PRIVATE  USE", f_cap,
                      (200, 180, 154), spacing_px=4, anchor="lm")

    return img


def section_dining(h=720):
    img = Image.new("RGB", (W, h), CREAM)
    d = ImageDraw.Draw(img)

    # Title strip
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (W // 2, 100), "DINING", f_eye, SUNSET, spacing_px=5, anchor="mm")
    d.line([(W // 2 - 22, 124), (W // 2 + 22, 124)], fill=SUNSET, width=1)
    f_h = ff(FONT_SERIF_IT, 50)
    d.text((W // 2, 190), "Tastes of the Setouchi.", font=f_h, fill=INK, anchor="mm")
    f_jp = ff(FONT_JP, 18)
    d.text((W // 2, 232), "瀬戸内と岡山の恵みを、火を囲んで。", font=f_jp, fill=INK_SOFT, anchor="mm")

    # Three-image grid
    grid_y = 290
    gap = 24
    cell_w = (W - 60 * 2 - gap * 2) // 3
    cell_h = 280

    # 1. BBQ — plate
    img_a = make_dining(cell_w, cell_h)
    img.paste(img_a, (60, grid_y))
    # 2. Breakfast — olive field
    img_b = make_olive_field(cell_w, cell_h)
    img.paste(img_b, (60 + cell_w + gap, grid_y))
    # 3. Bottle/seafood — sea horizon variant
    img_c = make_sea_horizon(cell_w, cell_h, sky_top=(244, 232, 216), sky_bot=(218, 200, 178),
                              sea_top=(160, 176, 174), sea_bot=(108, 130, 134),
                              horizon_at=0.62)
    img.paste(img_c, (60 + (cell_w + gap) * 2, grid_y))

    # Captions
    f_no = ff(FONT_SERIF_IT, 13)
    f_name_jp = ff(FONT_JP, 20)
    f_name_lt = ff(FONT_SERIF, 20)
    f_desc_jp = ff(FONT_JP, 12)
    f_desc_lt = ff(FONT_SERIF, 12)
    captions = [
        ("Course  01", "夕餉 — BBQ", "瀬戸内の魚介と岡山産野菜を、ヴィラのキッチンで。"),
        ("Course  02", "朝餉 — Morning", "岡山産の卵と季節野菜の、ゆっくりした朝。"),
        ("Local  03", "持ち寄り — Wine", "地元のワインやクラフトジンの持込もご自由に。"),
    ]
    for i, (no, name, desc) in enumerate(captions):
        x = 60 + i * (cell_w + gap)
        y = grid_y + cell_h + 22
        d.text((x, y), no, font=f_no, fill=SUNSET, anchor="lm")
        text_mixed(d, (x, y + 28), name, f_name_lt, f_name_jp, INK, anchor="lm")
        text_mixed(d, (x, y + 60), desc, f_desc_lt, f_desc_jp, INK_SOFT, anchor="lm")

    return img


def section_experience(h=520):
    img = Image.new("RGB", (W, h), SAND)
    d = ImageDraw.Draw(img)

    # Left: pull-quote layout
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (110, 140), "EXPERIENCE", f_eye, SUNSET, spacing_px=5, anchor="lm")
    d.line([(110, 162), (160, 162)], fill=SUNSET, width=1)

    f_h = ff(FONT_SERIF_IT, 56)
    d.text((110, 240), "Slow days,", font=f_h, fill=INK, anchor="lm")
    d.text((110, 308), "slower waves.", font=f_h, fill=INK, anchor="lm")

    f_jp = ff(FONT_JP, 18)
    d.text((110, 380), "牛窓・瀬戸内の過ごし方をご案内します。",
           font=f_jp, fill=INK_SOFT, anchor="lm")

    f_cap = ff(FONT_SERIF, 13)
    draw_letterspaced(d, (110, 430), "OLIVE PARK  /  CYCLE  /  SUNSET CRUISE",
                      f_cap, MUTED, spacing_px=4, anchor="lm")

    # Right: olive field image card
    img_w = 600
    img_h = 380
    px = W - 110 - img_w
    py = (h - img_h) // 2
    olive = make_olive_field(img_w, img_h)
    img.paste(olive, (px, py))
    d.rectangle([px, py, px + img_w, py + img_h], outline=(168, 152, 122), width=1)

    return img


def section_news(h=400):
    img = Image.new("RGB", (W, h), CREAM)
    d = ImageDraw.Draw(img)
    f_eye = ff(FONT_SERIF, 12)
    draw_letterspaced(d, (W // 2, 80), "NEWS  &  STORIES", f_eye, SUNSET, spacing_px=5, anchor="mm")
    d.line([(W // 2 - 28, 104), (W // 2 + 28, 104)], fill=SUNSET, width=1)
    # 3 news cards
    cards = [
        ("2026.04", "Spring stay plan.", "桜と潮風と、はじまりの春の特別プラン。"),
        ("2026.03", "Olive harvest.", "近くのオリーブ農園と新メニューの取り組み。"),
        ("2026.02", "Sauna refurb.", "サウナ室を再生木材でリニューアル。"),
    ]
    cell_w = 360
    gap = 30
    total = cell_w * 3 + gap * 2
    x0 = (W - total) // 2
    y0 = 160

    f_date = ff(FONT_SERIF_IT, 14)
    f_title = ff(FONT_SERIF, 22)
    f_jp_b = ff(FONT_JP, 13)
    for i, (date, title, jp) in enumerate(cards):
        x = x0 + i * (cell_w + gap)
        d.line([(x, y0 - 10), (x + cell_w, y0 - 10)], fill=SAND_DEEP, width=1)
        d.text((x, y0 + 0), date, font=f_date, fill=SUNSET, anchor="lm")
        d.text((x, y0 + 40), title, font=f_title, fill=INK, anchor="lm")
        d.text((x, y0 + 80), jp, font=f_jp_b, fill=INK_SOFT, anchor="lm")
        # read more arrow
        f_more = ff(FONT_SERIF_IT, 13)
        d.text((x, y0 + 140), "read  →", font=f_more, fill=SUNSET, anchor="lm")

    return img


def section_footer(h=420):
    img = Image.new("RGB", (W, h), SUMI)
    d = ImageDraw.Draw(img)

    # left — logo + tagline
    f_logo = ff(FONT_SERIF, 38)
    d.text((110, 110), "c o v o", font=f_logo, fill=WHITE, anchor="lm")
    f_under = ff(FONT_SERIF_IT, 16)
    d.text((110, 152), "— ushimado —", font=f_under, fill=(220, 200, 174), anchor="lm")
    f_jp = ff(FONT_JP, 13)
    f_lt = ff(FONT_SERIF, 13)
    text_mixed(d, (110, 200), "岡山県瀬戸内市牛窓町鹿忍 7195-1",
               f_lt, f_jp, (200, 192, 178), anchor="lm")
    d.text((110, 226), "Check-in 14:00  /  Check-out 10:00",
           font=ff(FONT_SERIF, 13), fill=(200, 192, 178), anchor="lm")

    # middle — nav columns
    cols = [
        ("STAY", ["Villa Anbai", "Villa Nagi", "Plans"]),
        ("EXPERIENCE", ["Sauna", "Dining", "Activity"]),
        ("INFORMATION", ["Access", "FAQ", "News"]),
    ]
    f_col_h = ff(FONT_SERIF, 12)
    f_col_i = ff(FONT_SERIF, 13)
    cx0 = 520
    for i, (head, items) in enumerate(cols):
        x = cx0 + i * 200
        draw_letterspaced(d, (x, 110), head, f_col_h, (220, 200, 174),
                          spacing_px=3, anchor="lm")
        d.line([(x, 130), (x + 28, 130)], fill=(180, 162, 136), width=1)
        for j, it in enumerate(items):
            d.text((x, 154 + j * 26), it, font=f_col_i, fill=(220, 214, 200), anchor="lm")

    # right — CTA
    cta_x = W - 110 - 280
    cta_y = 110
    d.rectangle([cta_x, cta_y, cta_x + 280, cta_y + 90], outline=(220, 200, 174), width=1)
    f_cta_s = ff(FONT_SERIF, 11)
    draw_letterspaced(d, (cta_x + 140, cta_y + 26), "RESERVATION", f_cta_s,
                      (220, 200, 174), spacing_px=3, anchor="mm")
    f_cta_b = ff(FONT_SERIF_IT, 22)
    d.text((cta_x + 140, cta_y + 60), "Book your stay  →", font=f_cta_b,
           fill=WHITE, anchor="mm")
    # contact link
    d.text((W - 110, cta_y + 130), "covo@ushimado.jp", font=ff(FONT_SERIF, 13),
           fill=(220, 200, 174), anchor="rm")
    d.text((W - 110, cta_y + 156), "+81  869  XX  XXXX", font=ff(FONT_SERIF, 13),
           fill=(220, 200, 174), anchor="rm")

    # bottom divider + copyright
    d.line([(110, h - 60), (W - 110, h - 60)], fill=(60, 56, 50), width=1)
    d.text((110, h - 32), "© 2026  COVO ushimado  /  ATELIER CUORE Inc.",
           font=ff(FONT_SERIF, 11), fill=(160, 152, 138), anchor="lm")
    draw_letterspaced(d, (W - 110, h - 32),
                      "INSTAGRAM   FACEBOOK   YOUTUBE",
                      ff(FONT_SERIF, 11), (160, 152, 138), spacing_px=3, anchor="rm")

    return img


# ============================================================
# Compose full page + save individual sections
# ============================================================
def main():
    sections = [
        ("01_hero", section_hero()),
        ("02_concept", section_intro()),
        ("03_stay", section_stay()),
        ("04_sauna", section_sauna()),
        ("05_dining", section_dining()),
        ("06_experience", section_experience()),
        ("07_news", section_news()),
        ("08_footer", section_footer()),
    ]

    # Save each section
    for name, im in sections:
        im2 = add_grain(im, amount=3)
        path = os.path.join(OUTDIR, f"covo_{name}.png")
        im2.save(path, "PNG", optimize=True)
        print(f"saved: {path}  {im2.size}")

    # Compose full page
    total_h = sum(im.height for _, im in sections)
    full = Image.new("RGB", (W, total_h), CREAM)
    y = 0
    for _, im in sections:
        full.paste(im, (0, y))
        y += im.height
    full = add_grain(full, amount=3)
    full_path = os.path.join(OUTDIR, "covo_full_page.png")
    full.save(full_path, "PNG", optimize=True)
    print(f"saved: {full_path}  {full.size}")


if __name__ == "__main__":
    main()
