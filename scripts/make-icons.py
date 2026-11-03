# -*- coding: utf-8 -*-
"""Z originálního loga (assets/logo/logo-vystaviste-flora.svg – znak + nápis, a assets/logo/logo-znak.svg – samotný znak)
vyrobí bílé varianty pro záhlaví aplikace a ikony PWA. Loga pocházejí z webu flora-ol.cz.
Usage: python -X utf8 scripts/make-icons.py
"""
import base64, io, re
from pathlib import Path
import numpy as np
import resvg_py
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / 'assets' / 'logo' / 'logo-vystaviste-flora.svg'
MARK = ROOT / 'assets' / 'logo' / 'logo-znak.svg'
GREEN = (59, 167, 61)        # #3ba73d – hlavní zelená webu
GREEN_DARK = (29, 94, 42)    # tmavší odstín pro pozadí ikon


def render(svg_path, width, color):
    """Vykreslí SVG (barva currentColor / černá → color) do RGBA."""
    svg = svg_path.read_text(encoding='utf-8')
    svg = svg.replace('currentColor', '#%02x%02x%02x' % color)
    # logo bez fill používá výchozí černou – přebarvíme přes atribut na kořeni symbolu
    if 'fill="none"' in svg: svg = svg.replace('fill="white"', 'fill="none"')  # znak: bílé výplně vynechat, zůstane jen tvar
    else: svg = re.sub(r'<symbol ', '<symbol fill="#%02x%02x%02x" ' % color, svg, count=1)
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=width))
    return Image.open(io.BytesIO(png)).convert('RGBA')


def recolor(img, rgb):
    out = Image.new('RGBA', img.size, rgb + (255,)); out.putalpha(img.getchannel('A')); return out


def split_logo(img):
    """Rozdělí svislé logo (znak nahoře, nápis dole) podle největší vodorovné mezery v alfa kanálu."""
    a = np.asarray(img.getchannel('A'))
    rows = np.where(a.max(axis=1) > 20)[0]
    gaps = np.diff(rows); i = int(gaps.argmax()); split = int((rows[i] + rows[i + 1]) // 2)
    mark = img.crop((0, 0, img.width, split)); mark = mark.crop(mark.getbbox())
    word = img.crop((0, split, img.width, img.height)); word = word.crop(word.getbbox())
    return mark, word


full = render(LOGO, 1600, (0, 0, 0))
mark_src, word_src = split_logo(full)
mark = render(MARK, 1024, (0, 0, 0))  # samostatný znak (bez vnitřních bílých výplní loga) má čistší hrany

def fit(img, w=None, h=None):
    if w: h = round(img.height * w / img.width)
    else: w = round(img.width * h / img.height)
    return img.resize((w, h), Image.LANCZOS)

# bílé varianty pro záhlaví (tmavě zelená lišta)
fit(recolor(mark, (255, 255, 255)), h=256).save(ROOT / 'assets' / 'logo-mark-white.png', optimize=True)
fit(recolor(word_src, (255, 255, 255)), w=900).save(ROOT / 'assets' / 'logo-word-white.png', optimize=True)
# zelené varianty (světlé pozadí)
fit(recolor(mark, GREEN), h=256).save(ROOT / 'assets' / 'logo-mark-green.png', optimize=True)
fit(recolor(word_src, (45, 65, 86)), w=900).save(ROOT / 'assets' / 'logo-word-slate.png', optimize=True)
# celé logo (znak + nápis) bílé a zelené, pro spořič a tisk
fit(recolor(full.crop(full.getbbox()), (255, 255, 255)), w=1200).save(ROOT / 'assets' / 'logo-full-white.png', optimize=True)
fit(recolor(full.crop(full.getbbox()), GREEN), w=1200).save(ROOT / 'assets' / 'logo-full-green.png', optimize=True)


def icon(size, maskable=False):
    S = size * 2
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    if maskable: d.rectangle([0, 0, S, S], fill=GREEN)
    else: d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 28 // 128, fill=GREEN)
    m = fit(recolor(mark, (255, 255, 255)), h=int(S * (0.52 if maskable else 0.66)))
    img.alpha_composite(m, ((S - m.width) // 2, (S - m.height) // 2))
    return img.resize((size, size), Image.LANCZOS)


icon(192).save(ROOT / 'assets' / 'icon-192.png', optimize=True)
icon(512).save(ROOT / 'assets' / 'icon-512.png', optimize=True)
icon(512, True).save(ROOT / 'assets' / 'icon-maskable-512.png', optimize=True)
# SVG ikona: zelený zaoblený čtverec s vloženým bílým znakem (vektor přímo ze symbolu)
mark_svg = MARK.read_text(encoding='utf-8')
inner = re.search(r'<symbol[^>]*>(.*?)</symbol>', mark_svg, re.S).group(1).replace('currentColor', '#ffffff')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="56" fill="#3ba73d"/>
  <g transform="translate(48 44) scale(1.6)">{inner}</g>
</svg>
'''
(ROOT / 'assets' / 'icon.svg').write_text(svg, encoding='utf-8')
print('icons ok, mark', mark.size, 'word', word_src.size)
