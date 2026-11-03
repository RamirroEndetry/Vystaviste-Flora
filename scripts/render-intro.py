# -*- coding: utf-8 -*-
"""Render the Výstaviště Flora Olomouc screensaver video (assets/intro/intro.mp4, 1920x1080) and its portrait cut
(assets/intro/intro-portrait.mp4, 1080x1920 for vertical info panels).

Uses the photos in assets/photos, the logo PNGs made by make-icons.py and data.js. Requires Pillow, numpy and ffmpeg on PATH.
Usage:
  python -X utf8 scripts/render-intro.py                 # landscape
  python -X utf8 scripts/render-intro.py --portrait      # portrait
  python -X utf8 scripts/render-intro.py --preview 2 7 12 16 21 25 28 --out <dir>   # PNG stills
"""
import json, math, random, subprocess, sys, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'intro'
PH = ROOT / 'assets' / 'photos'
PORTRAIT = '--portrait' in sys.argv
W, H = (1080, 1920) if PORTRAIT else (1920, 1080)
FPS, DURATION = 30, 30.0
NAME = 'intro-portrait' if PORTRAIT else 'intro'
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'

GREEN = np.array([59, 167, 61]) / 255
GREEN_DARK = np.array([18, 57, 27]) / 255
GREEN_DEEP = np.array([8, 30, 14]) / 255
GREEN_MID = np.array([35, 110, 45]) / 255
LIME = np.array([169, 198, 60]) / 255
GOLD = np.array([242, 193, 78]) / 255
CREAM = np.array([244, 247, 239]) / 255
WHITE = np.ones(3)

# ---- scénář (sekundy) ----
S_VYSTAVY, S_SKLENIKY, S_PARKY, S_AKCE, S_DOPRAVA, S_OUTRO = 4.5, 9.5, 14.0, 18.5, 23.0, 26.3
CUTS = [S_VYSTAVY, S_SKLENIKY, S_PARKY, S_AKCE, S_DOPRAVA, S_OUTRO]

rng = random.Random(7)
DATA = json.loads((ROOT / 'data.js').read_text(encoding='utf-8').split('= ', 1)[1].rstrip(';\n'))

# ---------- pomocné ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def out_expo(x): return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def out_cubic(x): return 1 - (1 - x) ** 3
def in_out(x): return 3 * x * x - 2 * x * x * x
def out_back(x, s=1.7): x -= 1; return 1 + x * x * ((s + 1) * x + s)

def font(size, style='Bold'):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_name(style)
    except Exception: pass
    return f

def to_sprite(img):
    a = np.asarray(img.convert('RGBA'), dtype=np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    return a

def blit(dst, spr, x, y, op=1.0):
    x, y = int(round(x)), int(round(y))
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1 or op <= 0: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    d *= 1 - s[..., 3:4] * op
    d += s[..., :3] * op

def add(dst, spr, x, y, op=1.0):
    x, y = int(round(x)), int(round(y))
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1 or op <= 0: return
    dst[y0:y1, x0:x1] += spr[y0 - y:y1 - y, x0 - x:x1 - x, :3] * op

def text_sprite(text, size, color=(255, 255, 255), style='Bold', spacing=0):
    f = font(size, style)
    chars = list(text)
    widths = [f.getlength(c) for c in chars]
    tw = int(sum(widths) + spacing * max(len(chars) - 1, 0)) + 12
    asc, desc = f.getmetrics()
    img = Image.new('L', (tw, asc + desc + 12), 0)
    d = ImageDraw.Draw(img)
    x = 6
    for c, cw in zip(chars, widths):
        d.text((x, 6), c, font=f, fill=255); x += cw + spacing
    img = img.crop(img.getbbox())
    rgba = Image.new('RGBA', img.size, tuple(int(c) for c in color) + (255,)); rgba.putalpha(img)
    return to_sprite(rgba)

def glow_of(spr, radius, color):
    a = Image.fromarray((spr[..., 3] * 255).astype(np.uint8))
    pad = radius * 3
    big = Image.new('L', (a.width + pad * 2, a.height + pad * 2)); big.paste(a, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(radius))
    g = np.asarray(big, np.float32)[..., None] / 255
    return np.concatenate([g * color, g * 0], axis=2).astype(np.float32), pad

def reveal(spr, p):
    w = int(spr.shape[1] * clamp(p))
    return spr[:, :w] if w > 0 else None

def center_blit(f, spr, y, op=1.0, p=1.0, dy=0.0, cx=None):
    s = reveal(spr, p)
    if s is not None: blit(f, s, (W / 2 if cx is None else cx) - spr.shape[1] / 2, y + dy, op)

def col(c): return tuple(int(round(v * 255)) for v in c)

_scaled = {}
def cache_scaled(spr, scale):
    key = (id(spr), round(scale, 3))
    if key not in _scaled:
        h, w = spr.shape[:2]
        im = Image.fromarray(np.clip(np.concatenate([spr[..., :3] / np.maximum(spr[..., 3:4], 1e-3), spr[..., 3:4]], 2) * 255, 0, 255).astype(np.uint8), 'RGBA')
        _scaled[key] = to_sprite(im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS))
    return _scaled[key]

# ---------- fotografie → dlaždice ----------
def photo_tile(name, tw=360, th=240, r=22, sh=26, label=None):
    """Fotografie oříznutá na poměr dlaždice, zaoblené rohy, měkký stín (RGBA sprite)."""
    src = PH / f'{name}.jpg'
    tile = Image.new('RGBA', (tw + sh * 2, th + sh * 2 + 10), (0, 0, 0, 0))
    shadow = Image.new('L', tile.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle([sh, sh + 10, sh + tw, sh + th + 10], radius=r, fill=130)
    shadow = shadow.filter(ImageFilter.GaussianBlur(13))
    tile.putalpha(shadow)
    if src.exists():
        im = ImageOps.fit(Image.open(src).convert('RGB'), (tw, th), Image.LANCZOS, centering=(0.5, 0.45)).convert('RGBA')
    else:
        im = Image.new('RGBA', (tw, th), col(GREEN_MID) + (255,))
    mask = Image.new('L', (tw, th), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, th - 1], radius=r, fill=255)
    if label:
        band = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
        bd.rectangle([0, th - 64, tw, th], fill=(8, 30, 14, 170))
        f = font(24, 'SemiBold'); bd.text((18, th - 46), label, font=f, fill=(255, 255, 255, 255))
        im.alpha_composite(band)
    card = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); card.paste(im, (0, 0), mask)
    tile.alpha_composite(card, (sh, sh))
    return to_sprite(tile)

print('Preparing tiles...')
TILES_VYSTAVY = [photo_tile(n) for n in ('flora-1', 'horti-1', 'flora-2', 'horti-3', 'flora-3', 'horti-2', 'flora-5', 'horti-5', 'flora-4', 'horti-4', 'horti-6', 'ev-flora-olomouc-2026', 'ev-hortikomplex-2026')]
TILES_SKLENIKY = [photo_tile(n, 330, 220) for n in ('skleniky-hero', 'skleniky-1', 'klenoty-1', 'skleniky-2', 'pasti-1', 'skleniky-3', 'skleniky-4', 'klenoty-2', 'skleniky-5', 'skleniky-6', 'skleniky-7', 'skleniky-exterier')]
TILES_PARKY = [photo_tile(n, 360, 240) for n in ('rozarium-hero', 'ruze-1', 'botanicka-hero', 'smetanovy-sady-hero', 'bezrucovy-vodopad', 'ruze-3', 'cechovy-hero', 'rozarium', 'botanicka-1', 'smetanovy-sady', 'bezrucovy-sady', 'ruze-2')]
UPCOMING = [e for e in DATA['events'] if e.get('image') and e['start'] >= '2026-11-01'][:6]
def short_date(e):
    d = e['start'].split('-'); m = ['led', 'úno', 'bře', 'dub', 'kvě', 'čer', 'čvc', 'srp', 'zář', 'říj', 'lis', 'pro'][int(d[1]) - 1]
    return f"{int(d[2])}. {m}" if e['start'] == e['end'] else f"{int(d[2])}.–{int(e['end'].split('-')[2])}. {m}"
def short_title(t):
    t = re.sub(r'\s+[–-]\s+.*$', '', t); t = re.sub(r'\s+\d{4}$', '', t)
    return t if len(t) <= 20 else t[:19].rstrip() + '…'
TILES_AKCE = [photo_tile(Path(e['image']).stem, 400, 266, label=f"{short_date(e)}  ·  {short_title(e['title'])}") for e in UPCOMING]
print(f'  {len(TILES_VYSTAVY)} / {len(TILES_SKLENIKY)} / {len(TILES_PARKY)} / {len(TILES_AKCE)} tiles')

# ---------- logo (bílé PNG z make-icons.py) ----------
MARK_IMG0 = Image.open(ROOT / 'assets' / 'logo-mark-white.png').convert('RGBA')
WORD_IMG0 = Image.open(ROOT / 'assets' / 'logo-word-white.png').convert('RGBA')
def fit(im, width=None, height=None):
    if width: height = round(im.height * width / im.width)
    else: width = round(im.width * height / im.height)
    return im.resize((max(1, width), max(1, height)), Image.LANCZOS)
MARK_H = 460 if PORTRAIT else 380
MARK_IMG = fit(MARK_IMG0, height=MARK_H)
MARK = to_sprite(MARK_IMG)
WORD_IMG = fit(WORD_IMG0, width=int(W * (0.66 if PORTRAIT else 0.34)))
WORD = to_sprite(WORD_IMG)
MARK_GLOW, MARK_GLOW_PAD = glow_of(MARK, 40, LIME * 0.45 + GOLD * 0.25)
BIG_MARK = fit(MARK_IMG0, height=1300).getchannel('A').filter(ImageFilter.GaussianBlur(6))
_pad = Image.new('L', (1600, 1600), 0); _pad.paste(BIG_MARK, ((1600 - BIG_MARK.width) // 2, (1600 - BIG_MARK.height) // 2)); BIG_MARK = _pad

def big_mark(angle, op):
    r = np.asarray(BIG_MARK.rotate(angle, resample=Image.BILINEAR), np.float32)[..., None] / 255
    return np.concatenate([r * (LIME * 0.9) * op, r * 0], axis=2)

# ---------- texty ----------
def eyebrow(t, color=LIME, size=30): return text_sprite(t, size, col(color), 'SemiBold', spacing=10)
def headline(t, size): return text_sprite(t, size, (255, 255, 255), 'Bold', spacing=2)
def sub(t, size=38): return text_sprite(t, size, col(CREAM * 0.94), 'Light', spacing=1)

HL = 104 if PORTRAIT else 112
T = dict(
    eyebrow=eyebrow('VÝSTAVY  ·  PARKY  ·  SKLENÍKY  ·  ROZÁRIUM', LIME, 24 if PORTRAIT else 30),
    vystavy_eb=eyebrow('FLORA OLOMOUC  ·  JARO A PODZIM'),
    skleniky_eb=eyebrow('SBÍRKOVÉ SKLENÍKY  ·  SMETANOVY SADY'),
    parky_eb=eyebrow('ROZÁRIUM  ·  BOTANICKÁ ZAHRADA  ·  PARKY'),
    akce_eb=eyebrow('CO SE CHYSTÁ'),
    doprava_eb=eyebrow('JAK SE K NÁM DOSTAT'),
    outro_eb=eyebrow('TĚŠÍME SE NA VÁS'),
)
if PORTRAIT:
    T['vystavy_h'] = [headline('NEJVĚTŠÍ', HL), headline('SVÁTEK', HL), headline('KVĚTIN', HL)]
    T['vystavy_s'] = [sub('Flora Olomouc  ·  přes 50 let tradice'), sub('300+ prodejců na zahradnických trzích')]
    T['skleniky_h'] = [headline('PALMY, KAKTUSY', HL), headline('A VIKTORIE', HL)]
    T['skleniky_s'] = [sub('4 100 m²  ·  palmový skleník z roku 1927'), sub('Út–Ne 9:00–18:00  ·  v zimě So–Ne')]
    T['parky_h'] = [headline('4 500 KEŘŮ', HL), headline('RŮŽÍ', HL)]
    T['parky_s'] = [sub('rozárium a botanická zahrada  ·  vstup zdarma'), sub('50 ha historických parků v centru města')]
    T['akce_h'] = [headline('VELETRHY, TRHY', HL), headline('A KONCERTY', HL)]
    T['akce_s'] = [sub('pavilon A  ·  vstupenky online levněji')]
    T['doprava_h'] = [headline('TRAMVAJÍ', HL), headline('PŘÍMO', HL), headline('K PAVILONU A', HL)]
    T['doprava_s'] = [sub('zastávka Výstaviště Flora'), sub('P6 Šantovka při akcích zdarma')]
    T['outro_h'] = [headline('VÍTEJTE', 118)]
else:
    T['vystavy_h'] = [headline('NEJVĚTŠÍ SVÁTEK KVĚTIN', HL)]
    T['vystavy_s'] = [sub('Flora Olomouc  ·  jaro a podzim  ·  přes 50 let tradice  ·  300+ prodejců')]
    T['skleniky_h'] = [headline('PALMY, KAKTUSY A VIKTORIE', HL)]
    T['skleniky_s'] = [sub('4 100 m² sbírkových skleníků  ·  palmový skleník z roku 1927  ·  Út–Ne 9:00–18:00')]
    T['parky_h'] = [headline('4 500 KEŘŮ RŮŽÍ', HL)]
    T['parky_s'] = [sub('rozárium a botanická zahrada zdarma  ·  50 ha historických parků v centru Olomouce')]
    T['akce_h'] = [headline('VELETRHY, TRHY A KONCERTY', HL)]
    T['akce_s'] = [sub('pavilon A  ·  vstupenky online levněji  ·  akce.flora-ol.cz')]
    T['doprava_h'] = [headline('TRAMVAJÍ PŘÍMO K PAVILONU A', HL)]
    T['doprava_s'] = [sub('zastávka Výstaviště Flora  ·  parkoviště P6 Šantovka při akcích zdarma')]
    T['outro_h'] = [headline('VÍTEJTE', 118)]
TRAMS = [text_sprite(n, 72, col(GREEN_DEEP), 'Bold') for n in ('1', '4', '6')]
BUSES = [text_sprite(n, 44, col(GREEN_DEEP), 'Bold') for n in ('16', '17', '28', '51')]
T_TRAM_EB = eyebrow('TRAMVAJE', CREAM * 0.9, 26)
T_BUS_EB = eyebrow('AUTOBUSY  ·  SMETANOVY SADY', CREAM * 0.9, 26)
CHIP_TXT = [text_sprite(s, 30, col(GREEN_DEEP), 'SemiBold', spacing=3) for s in ('VELETRHY', 'KONCERTY', 'TRHY', 'FESTIVALY', 'VÝSTAVY', 'SPORT')]
SK_TXT = [text_sprite(s, 30, col(GREEN_DEEP), 'SemiBold', spacing=3) for s in ('PALMOVÝ', 'KAKTUSOVÝ', 'TROPICKÝ', 'SUBTROPICKÝ')]

def chip(txt_spr, color=LIME, padx=26, pady=14):
    h, w = txt_spr.shape[:2]
    im = Image.new('RGBA', (w + padx * 2, h + pady * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=col(color) + (255,))
    spr = to_sprite(im); blit_into(spr, txt_spr, padx, pady); return spr

def blit_into(dst, spr, x, y):
    h, w = spr.shape[:2]
    d = dst[y:y + h, x:x + w]
    d *= 1 - spr[..., 3:4]; d += spr
CHIPS = [chip(c, LIME if i % 2 == 0 else CREAM) for i, c in enumerate(CHIP_TXT)]
SK_CHIPS = [chip(c, LIME if i % 2 == 0 else CREAM) for i, c in enumerate(SK_TXT)]
TRAM_BADGES = [chip(t, GOLD, 34, 18) for t in TRAMS]
BUS_BADGES = [chip(t, CREAM, 22, 12) for t in BUSES]
P6 = chip(text_sprite('P6  ŠANTOVKA  ·  ZDARMA PŘI AKCÍCH', 30, col(GREEN_DEEP), 'Bold', spacing=4), LIME, 30, 16)

# ---------- pozadí ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
rad = np.sqrt(nx ** 2 * (0.75 if not PORTRAIT else 1.1) + (ny + 0.1) ** 2)
base = GREEN_DEEP * 0.9 + (GREEN_MID - GREEN_DEEP) * np.clip(1.15 - rad, 0, 1)[..., None] * 0.9
vign = np.clip(1 - 0.5 * (nx ** 2 * 0.6 + ny ** 2 * 0.9), 0.3, 1)[..., None]
noise = np.asarray(Image.effect_noise((W // 3, H // 3), 30).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
BG = (base * vign * (0.9 + 0.2 * noise)).astype(np.float32)
BG += (LIME * 0.07)[None, None] * np.clip(1 - np.sqrt((nx - 0.6) ** 2 + (ny + 1.1) ** 2) / 1.1, 0, 1)[..., None]

def soft_disc(r, color):
    s = r * 2 + 2
    yy2, xx2 = np.mgrid[0:s, 0:s] - r
    d = np.sqrt(xx2 ** 2 + yy2 ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 1.6
    return np.concatenate([a[..., None] * color, a[..., None] * 0], axis=2).astype(np.float32)
BOKEH = [(soft_disc(r, LIME * 0.9 if i % 3 else GOLD * 0.8), rng.uniform(0, W), rng.uniform(0, H), rng.uniform(8, 20), rng.uniform(0, 6.28), 0.04 + rng.uniform(0, 0.05))
         for i, r in enumerate([rng.randrange(60, 220) for _ in range(14)])]
DOTS = [soft_disc(r, WHITE * 0.7 + LIME * 0.5) for r in (2, 3, 5)]
SPARK = [[rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.3, 1)] for _ in range(90)]

def backdrop(f, t):
    for spr, x, y, speed, ph, op in BOKEH:
        px = (x + math.sin(t * 0.13 + ph) * 90) % (W + 400) - 200
        py = (y - t * speed) % (H + 400) - 200
        add(f, spr, px - spr.shape[1] / 2, py - spr.shape[0] / 2, op * (0.8 + 0.2 * math.sin(t * 0.9 + ph)))
    add(f, big_mark(t * 2.0, 0.05), W * (0.72 if not PORTRAIT else 0.5) - 800, H * 0.5 - 800 + math.sin(t * 0.3) * 20)
    for x, y, z in SPARK:
        px = (x + math.sin(t * 0.5 + y) * 25) % W; py = (y - t * 18 * z) % H
        add(f, DOTS[0 if z < 0.7 else 1], px, py, 0.35 * z)

_bands = {}
def legibility_band(f, y0, y1, strength=0.55):
    key = (y0, y1, strength)
    if key not in _bands:
        a = np.clip(np.minimum((yy - y0) / 90, (y1 - yy) / 90), 0, 1)[..., None] * strength
        _bands[key] = (1 - a, GREEN_DEEP[None, None] * a * 0.9)
    m, c = _bands[key]
    f *= m; f += c

# ---------- scény ----------
def rows_of_tiles(f, lt, tiles, rows, y_top, gap_y, speed, tile_op, scale=1.0):
    """Pásy dlaždic plující v protisměru (paralaxa)."""
    n = len(tiles)
    for r in range(rows):
        dir_ = 1 if r % 2 == 0 else -1
        spr0 = tiles[0]; th, tw = spr0.shape[:2]
        tw_s = int(tw * scale)
        step = tw_s + 20
        off = (lt * speed * (0.75 + 0.25 * (r % 3)) * dir_ + r * 170) % step
        y = y_top + r * (int(th * scale) + gap_y)
        count = W // step + 3
        for i in range(-1, count):
            spr = tiles[(i + r * 5) % n]
            if scale != 1.0: spr = cache_scaled(spr, scale)
            x = i * step + off - step
            blit(f, spr, x, y, tile_op)

def draw_block(f, lt, eb, heads, subs, y, t0=0.2, cx=None):
    """Eyebrow + nadpisy + podtitulky s postupným odhalením. Vrací spodní y."""
    cx = W / 2 if cx is None else cx
    a = out_expo(prog(lt, t0, t0 + 0.6))
    if a > 0:
        line = int(90 * a)
        f[int(y) + 14:int(y) + 17, int(cx - line / 2):int(cx + line / 2)] += LIME * 0.9
        center_blit(f, eb, y + 32, a, 1.0, (1 - a) * 16, cx)
    yy0 = y + 95
    for k, h in enumerate(heads):
        p = prog(lt, t0 + 0.25 + k * 0.18, t0 + 0.95 + k * 0.18)
        center_blit(f, h, yy0, 1.0, out_expo(p), (1 - out_expo(p)) * 26, cx)
        yy0 += h.shape[0] + 14
    yy0 += 12
    for k, s in enumerate(subs):
        p = prog(lt, t0 + 0.8 + k * 0.15, t0 + 1.4 + k * 0.15)
        if p > 0: center_blit(f, s, yy0, p, 1.0, (1 - out_cubic(p)) * 18, cx)
        yy0 += s.shape[0] + 16
    return yy0

def chip_row(f, lt, chips, y, t0, rows_portrait=2):
    """Řada (nebo dvě řady na výšku) „chipů“ s pružným naskočením."""
    groups = [chips]
    if PORTRAIT and len(chips) > 3:
        half = (len(chips) + 1) // 2; groups = [chips[:half], chips[half:]]
    for gi, items in enumerate(groups):
        total = sum(c.shape[1] for c in items) + 16 * (len(items) - 1)
        x = W / 2 - total / 2
        for i, ch in enumerate(items):
            k = i + gi * len(groups[0])
            p = out_back(prog(lt, t0 + k * 0.12, t0 + 0.6 + k * 0.12), 1.2)
            if p > 0:
                s = cache_scaled(ch, max(0.05, p)) if p < 0.999 else ch
                blit(f, s, x + (ch.shape[1] - s.shape[1]) / 2, y + gi * (ch.shape[0] + 14) + (ch.shape[0] - s.shape[0]) / 2, clamp(p))
            x += ch.shape[1] + 16

def scene_intro(f, t):
    lt = t
    cx, cy = W / 2, (H * 0.33 if PORTRAIT else H * 0.36)
    e = out_back(prog(lt, 0.3, 1.3), 1.1)
    if e > 0:
        sc = 0.3 + 0.7 * e; ang = (1 - e) * -50
        if abs(e - 1) < 0.002: spr = MARK
        else:
            im = MARK_IMG.rotate(ang, resample=Image.BICUBIC, expand=True)
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
            spr = to_sprite(im)
        if lt > 1.1: add(f, MARK_GLOW, cx - MARK.shape[1] / 2 - MARK_GLOW_PAD, cy - MARK.shape[0] / 2 - MARK_GLOW_PAD, (0.55 + 0.2 * math.sin(lt * 2)) * prog(lt, 1.1, 1.9))
        blit(f, spr, cx - spr.shape[1] / 2, cy - spr.shape[0] / 2, prog(lt, 0.3, 0.7))
        gp = prog(lt, 1.9, 2.7)
        if 0 < gp < 1 and spr is MARK:
            mh, mw = MARK.shape[:2]
            band = Image.new('L', (mw, mh), 0); d = ImageDraw.Draw(band)
            bx = -200 + gp * (mw + 400)
            d.polygon([(bx, 0), (bx + 70, 0), (bx - 90, mh), (bx - 160, mh)], fill=255)
            band = np.asarray(band.filter(ImageFilter.GaussianBlur(12)), np.float32) / 255
            g = (band * MARK[..., 3])[..., None]
            x0, y0 = int(cx - mw / 2), int(cy - mh / 2)
            f[y0:y0 + mh, x0:x0 + mw] += g * (LIME * 0.5 + WHITE * 0.3)
    # nápis „Výstaviště Flora Olomouc“ (originál) se odkrývá zleva doprava
    by = cy + MARK.shape[0] / 2 + (56 if PORTRAIT else 44)
    a = out_expo(prog(lt, 1.2, 2.0))
    center_blit(f, WORD, by, 1.0, a, (1 - a) * 30)
    e2 = prog(lt, 1.9, 2.6)
    if e2 > 0:
        ln = int((WORD.shape[1] * 0.9) * out_expo(e2))
        yl = int(by) + WORD.shape[0] + 30
        f[yl:yl + 2, int(cx - ln / 2):int(cx + ln / 2)] += LIME * 0.9
        center_blit(f, T['eyebrow'], by + WORD.shape[0] + 52, e2, 1.0, (1 - out_cubic(e2)) * 14)
    fl = 1 - prog(lt, 1.1, 1.6)
    if lt > 1.05: f += (LIME * 0.3 + WHITE * 0.25) * max(0, fl) ** 2 * 0.6

def scene_vystavy(f, t):
    lt = t - S_VYSTAVY
    e = out_expo(prog(lt, 0, 1.2))
    if PORTRAIT:
        rows_of_tiles(f, lt + 6, TILES_VYSTAVY, 4, int(H * 0.40) + int((1 - e) * 200), 22, 55, 0.96 * e, 0.92)
        legibility_band(f, -200, int(H * 0.38), 0.35)
        draw_block(f, lt, T['vystavy_eb'], T['vystavy_h'], T['vystavy_s'], H * 0.08)
    else:
        rows_of_tiles(f, lt + 6, TILES_VYSTAVY, 2, int(H * 0.47) + int((1 - e) * 200), 26, 70, 0.96 * e, 1.0)
        legibility_band(f, -200, int(H * 0.45), 0.35)
        draw_block(f, lt, T['vystavy_eb'], T['vystavy_h'], T['vystavy_s'], H * 0.10)

def scene_skleniky(f, t):
    lt = t - S_SKLENIKY
    e = out_expo(prog(lt, 0, 1.2))
    sc = (0.78 if PORTRAIT else 0.9) * (1 + lt * 0.012)
    spr0 = cache_scaled(TILES_SKLENIKY[0], sc); th, tw = spr0.shape[:2]
    cols = 3 if PORTRAIT else 6
    rows = 4 if PORTRAIT else 2
    gx, gy = tw + 16, th + 16
    x0 = W / 2 - (cols * gx) / 2 + 8 + math.sin(lt * 0.4) * 30
    y0 = (H * 0.47 if PORTRAIT else H * 0.46) + (1 - e) * 240
    k = 0
    for r in range(rows):
        for c in range(cols):
            spr = cache_scaled(TILES_SKLENIKY[(k * 5) % len(TILES_SKLENIKY)], sc); k += 1
            d = prog(lt, 0.05 * (c + r * 2), 0.5 + 0.05 * (c + r * 2))
            blit(f, spr, x0 + c * gx + (r % 2) * gx * 0.5 - gx * 0.25, y0 + r * gy + (1 - out_expo(d)) * 60, out_expo(d) * 0.97)
    legibility_band(f, -200, int(H * (0.44 if PORTRAIT else 0.43)), 0.4)
    yb = draw_block(f, lt, T['skleniky_eb'], T['skleniky_h'], T['skleniky_s'], H * 0.07 if PORTRAIT else H * 0.10)
    chip_row(f, lt, SK_CHIPS, yb + 18, 1.5)

def scene_parky(f, t):
    lt = t - S_PARKY
    e = out_expo(prog(lt, 0, 1.2))
    if PORTRAIT:
        rows_of_tiles(f, lt + 3, TILES_PARKY, 4, int(H * 0.40) + int((1 - e) * 200), 22, 48, 0.96 * e, 0.92)
        legibility_band(f, -200, int(H * 0.38), 0.35)
        draw_block(f, lt, T['parky_eb'], T['parky_h'], T['parky_s'], H * 0.08)
    else:
        rows_of_tiles(f, lt + 3, TILES_PARKY, 2, int(H * 0.47) + int((1 - e) * 200), 26, 60, 0.96 * e, 1.0)
        legibility_band(f, -200, int(H * 0.45), 0.35)
        draw_block(f, lt, T['parky_eb'], T['parky_h'], T['parky_s'], H * 0.10)

def scene_akce(f, t):
    lt = t - S_AKCE
    e = out_expo(prog(lt, 0, 1.2))
    tiles = TILES_AKCE
    if PORTRAIT:
        sc = 0.78; spr0 = cache_scaled(tiles[0], sc); th, tw = spr0.shape[:2]
        cols, gx, gy = 2, tw + 14, th + 14
        x0 = W / 2 - cols * gx / 2 + 7; y0 = H * 0.42 + (1 - e) * 200
        for i, tl in enumerate(tiles):
            r, c = divmod(i, cols); d = prog(lt, 0.1 * i, 0.6 + 0.1 * i)
            blit(f, cache_scaled(tl, sc), x0 + c * gx, y0 + r * gy + (1 - out_expo(d)) * 60, out_expo(d) * 0.97)
        legibility_band(f, -200, int(H * 0.40), 0.35)
        yb = draw_block(f, lt, T['akce_eb'], T['akce_h'], T['akce_s'], H * 0.08)
        chip_row(f, lt, CHIPS, yb + 14, 1.4)
    else:
        sc = 0.8; spr0 = cache_scaled(tiles[0], sc); th, tw = spr0.shape[:2]
        cols, gx, gy = 3, tw + 14, th - 30
        x0 = W / 2 - cols * gx / 2 + 7; y0 = H * 0.465 + (1 - e) * 200
        for i, tl in enumerate(tiles):
            r, c = divmod(i, cols); d = prog(lt, 0.1 * i, 0.6 + 0.1 * i)
            blit(f, cache_scaled(tl, sc), x0 + c * gx + (r % 2) * 30 - 15, y0 + r * gy + (1 - out_expo(d)) * 60, out_expo(d) * 0.97)
        legibility_band(f, -200, int(H * 0.47), 0.35)
        yb = draw_block(f, lt, T['akce_eb'], T['akce_h'], T['akce_s'], H * 0.10)
        chip_row(f, lt, CHIPS, yb + 14, 1.4)

def scene_doprava(f, t):
    lt = t - S_DOPRAVA
    horizon = H * (0.52 if PORTRAIT else 0.50)
    lines = Image.new('L', (W, H), 0); d = ImageDraw.Draw(lines)
    # koleje: dvě dvojice ubíhající do dálky
    for off in (-1, 1):
        for k in (0.75, 1.0):
            d.line([(W / 2 + off * 22 * k, horizon), (W / 2 + off * (330 if PORTRAIT else 520) * k, H + 100)], fill=90, width=3)
    for k in range(1, 12):
        yk = horizon + ((k + (lt * 1.1) % 1) ** 2.1) * (H - horizon) / 55
        if yk < H:
            wd = (W / 2) * (yk - horizon) / (H - horizon) * (1.3 if PORTRAIT else 1.1)
            d.line([(W / 2 - wd, yk), (W / 2 + wd, yk)], fill=int(40 + 90 * (k / 12)), width=2 + k // 3)
    arr = np.asarray(lines.filter(ImageFilter.GaussianBlur(1.0)), np.float32)[..., None] / 255
    f += arr * (LIME * 0.5 + GOLD * 0.2) * prog(lt, 0, 1.0)
    # světlo tramvaje projíždějící
    p = prog(lt, 0.5, 2.6)
    if 0 < p < 1:
        px = -300 + out_cubic(p) * (W + 600); py = horizon + 120 + p * 80
        tail = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(tail)
        for ln, wd, fill in ((700, 4, 90), (380, 10, 150), (160, 20, 255)):
            dd.line([(px - ln, py + ln * 0.06), (px, py)], fill=fill, width=wd)
        tail = np.asarray(tail.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255
        f += tail * (GOLD * 0.8 + WHITE * 0.4)
    legibility_band(f, -200, int(horizon) - 20, 0.3)
    yb = draw_block(f, lt, T['doprava_eb'], T['doprava_h'], T['doprava_s'], H * 0.07 if PORTRAIT else H * 0.10)
    # tramvajové linky
    a = prog(lt, 0.8, 1.4)
    if a > 0:
        total = sum(b.shape[1] for b in TRAM_BADGES) + 22 * 2
        ty = H * 0.62 if PORTRAIT else H * 0.63
        center_blit(f, T_TRAM_EB, ty - 56, a)
        x = W / 2 - total / 2
        for i, b in enumerate(TRAM_BADGES):
            q = out_back(prog(lt, 1.0 + i * 0.12, 1.5 + i * 0.12), 1.3)
            if q > 0:
                s = cache_scaled(b, max(0.05, q)) if q < 0.999 else b
                gl, gpad = glow_of(b, 24, GOLD * 0.7)
                add(f, gl, x - gpad, ty - gpad, 0.4 * clamp(q))
                blit(f, s, x + (b.shape[1] - s.shape[1]) / 2, ty + (b.shape[0] - s.shape[0]) / 2, clamp(q))
            x += b.shape[1] + 22
    a2 = prog(lt, 1.7, 2.2)
    if a2 > 0:
        total = sum(b.shape[1] for b in BUS_BADGES) + 14 * 3
        by = H * 0.74 if PORTRAIT else H * 0.78
        center_blit(f, T_BUS_EB, by - 48, a2)
        x = W / 2 - total / 2
        for i, b in enumerate(BUS_BADGES):
            q = out_back(prog(lt, 1.8 + i * 0.1, 2.3 + i * 0.1), 1.3)
            if q > 0:
                s = cache_scaled(b, max(0.05, q)) if q < 0.999 else b
                blit(f, s, x + (b.shape[1] - s.shape[1]) / 2, by + (b.shape[0] - s.shape[0]) / 2, clamp(q))
            x += b.shape[1] + 14
    q = out_back(prog(lt, 2.3, 2.9), 1.2)
    if q > 0:
        s = cache_scaled(P6, max(0.05, q)) if q < 0.999 else P6
        blit(f, s, W / 2 - s.shape[1] / 2, (H * 0.86 if PORTRAIT else H * 0.90) - s.shape[0] / 2, clamp(q))

def make_rays(size, n):
    im = Image.new('L', (size, size), 0); d = ImageDraw.Draw(im); c = size / 2
    for i in range(n):
        a0 = i * 2 * math.pi / n; a1 = a0 + math.pi / n * 0.5
        d.polygon([(c, c), (c + math.cos(a0) * c * 1.5, c + math.sin(a0) * c * 1.5), (c + math.cos(a1) * c * 1.5, c + math.sin(a1) * c * 1.5)], fill=255)
    im = im.filter(ImageFilter.GaussianBlur(14))
    yy2, xx2 = np.mgrid[0:size, 0:size]; r = np.sqrt((xx2 - c) ** 2 + (yy2 - c) ** 2) / c
    return Image.fromarray((np.asarray(im, np.float32) * np.clip(1 - r, 0, 1) ** 1.3).astype(np.uint8))
RAYS = make_rays(1900, 16)
def rays_sprite(angle, op, color):
    r = np.asarray(RAYS.rotate(angle, resample=Image.BILINEAR), np.float32)[..., None] / 255
    return np.concatenate([r * color * op, r * 0], axis=2)

def scene_outro(f, t):
    lt = t - S_OUTRO
    cx, cy = W / 2, H * (0.30 if PORTRAIT else 0.30)
    add(f, rays_sprite(-lt * 5, 0.35 * prog(lt, 0, 1.0), LIME * 0.5 + GOLD * 0.4), cx - 950, cy - 950)
    e = prog(lt, 0, 0.9)
    sc = (1.5 - 0.5 * out_back(e, 1.2)) if e < 1 else 1.0
    sc *= 1 + 0.01 * math.sin(lt * 1.8)
    base = 0.85
    spr = cache_scaled(MARK, base) if abs(sc - 1) < 0.002 else to_sprite(MARK_IMG.resize((max(1, int(MARK_IMG.width * base * sc)), max(1, int(MARK_IMG.height * base * sc))), Image.BILINEAR))
    add(f, MARK_GLOW, cx - MARK.shape[1] / 2 - MARK_GLOW_PAD, cy - MARK.shape[0] / 2 - MARK_GLOW_PAD, (0.5 + 0.2 * math.sin(lt * 2.2)) * prog(lt, 0.3, 1.0))
    blit(f, spr, cx - spr.shape[1] / 2, cy - spr.shape[0] / 2, prog(lt, 0, 0.3))
    word = cache_scaled(WORD, 0.85)
    by = cy + MARK.shape[0] * base / 2 + (48 if PORTRAIT else 36)
    p = out_expo(prog(lt, 0.6, 1.3))
    center_blit(f, word, by, 1.0, p, (1 - p) * 24)
    by += word.shape[0] + (70 if PORTRAIT else 54)
    for k, h in enumerate(T['outro_h']):
        p = out_expo(prog(lt, 1.1 + k * 0.2, 1.8 + k * 0.2))
        center_blit(f, h, by, 1.0, p, (1 - p) * 28); by += h.shape[0] + 14
    p2 = prog(lt, 1.6, 2.2)
    if p2 > 0:
        ln = int(260 * out_expo(p2)); f[int(by) + 16:int(by) + 18, int(cx - ln / 2):int(cx + ln / 2)] += LIME
        center_blit(f, T['outro_eb'], by + 36, p2, 1.0, (1 - out_cubic(p2)) * 12)
    fl = 1 - prog(lt, 0.0, 0.5)
    if fl > 0: f += (LIME * 0.3 + WHITE * 0.3) * fl ** 2 * 0.5

SCENES = [(0.0, scene_intro), (S_VYSTAVY, scene_vystavy), (S_SKLENIKY, scene_skleniky), (S_PARKY, scene_parky), (S_AKCE, scene_akce), (S_DOPRAVA, scene_doprava), (S_OUTRO, scene_outro)]

def scene_at(t):
    cur = SCENES[0][1]
    for start, fn in SCENES:
        if t >= start: cur = fn
    return cur

def wipe(f, t):
    """Limetková linka a zelený pás, které zakryjí střih mezi scénami."""
    for c in CUTS:
        p = (t - (c - 0.28)) / 0.56
        if 0 <= p <= 1:
            if PORTRAIT:
                y = -800 + in_out(p) * (H + 1600)
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(0, y), (W, y - 260), (W, y + 440), (0, y + 700)], fill=255)
                e = Image.new('L', (W, H), 0); de = ImageDraw.Draw(e)
                de.line([(0, y + 700), (W, y + 440)], fill=255, width=10); de.line([(0, y), (W, y - 260)], fill=255, width=10)
            else:
                x = -1300 + in_out(p) * (W + 2600)
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(x, 0), (x + 1000, 0), (x + 1000 - 420, H), (x - 420, H)], fill=255)
                e = Image.new('L', (W, H), 0); de = ImageDraw.Draw(e)
                de.line([(x + 1000, 0), (x + 580, H)], fill=255, width=10); de.line([(x, 0), (x - 420, H)], fill=255, width=10)
            e = e.filter(ImageFilter.GaussianBlur(5))
            ma = np.asarray(m, np.float32)[..., None] / 255
            colr = GREEN * (0.75 + 0.25 * (1 - ny[..., None] ** 2))
            f[:] = f * (1 - ma) + colr * ma
            f += np.asarray(e, np.float32)[..., None] / 255 * (LIME * 0.9 + WHITE * 0.2)

def render(t):
    f = BG.copy()
    backdrop(f, t)
    scene_at(t)(f, t)
    wipe(f, t)
    fade = min(prog(t, 0, 0.7), 1 - prog(t, DURATION - 0.8, DURATION))
    f *= fade
    return np.clip(f * 255, 0, 255).astype(np.uint8)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if '--preview' in sys.argv:
        dest = Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else Path('.')
        times = [float(x) for x in sys.argv[sys.argv.index('--preview') + 1:] if re.match(r'^[\d.]+$', x)]
        for t in times:
            Image.fromarray(render(t)).save(dest / f'preview-{NAME}-{t:05.1f}.png')
        print('previews:', dest); return
    frames = int(DURATION * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT / f'{NAME}.mp4')]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    poster = None
    for k in range(frames):
        t = k / FPS
        fr = render(t)
        if abs(t - (S_OUTRO + 2.6)) < 0.5 / FPS: poster = fr
        proc.stdin.write(fr.tobytes())
        if k % 60 == 0: print(f'frame {k}/{frames}', flush=True)
    proc.stdin.close(); proc.wait()
    if poster is not None: Image.fromarray(poster).save(OUT / f'{NAME}-poster.jpg', quality=85)
    # WebM (VP9) pro Chromium bez H.264
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(OUT / f'{NAME}.mp4'), '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '33', '-row-mt', '1', '-an', str(OUT / f'{NAME}.webm')])
    print('Done:', OUT / f'{NAME}.mp4')

if __name__ == '__main__':
    main()
