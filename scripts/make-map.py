# -*- coding: utf-8 -*-
"""Sestaví mapu okolí výstaviště (assets/map/okoli.jpg) z dlaždic OpenStreetMap a uloží data/map.json
(mapování zeměpisných souřadnic na pixely), ze kterého build-data.py doplní polohu míst a parkovišť.
Mapa je uložená v aplikaci, aby navigace fungovala i bez internetu a bez odchodu z aplikace (režim infopanelu).
Usage: python -X utf8 scripts/make-map.py
Data © přispěvatelé OpenStreetMap (ODbL) – atribuce je zobrazená v aplikaci. Dlaždice stahujeme jednorázově (cca 170 ks).
"""
import io, json, math, time, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'map'
ZOOM = 17
# výřez: Čechovy sady – výstaviště – Šantovka – rozárium – Bezručovy sady
LON0, LON1, LAT0, LAT1 = 17.232, 17.2705, 49.5835, 49.6005
TILE = 256


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def fetch(z, x, y):
    url = f'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    req = urllib.request.Request(url, headers={'User-Agent': 'vystaviste-flora-app/1.0 (prototype infopanel map; martin@tripon.cz)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert('RGB')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x0, y1 = tile_xy(LON0, LAT0, ZOOM); x1, y0 = tile_xy(LON1, LAT1, ZOOM)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    cols, rows = tx1 - tx0 + 1, ty1 - ty0 + 1
    img = Image.new('RGB', (cols * TILE, rows * TILE), (235, 235, 230))
    print(f'{cols}x{rows} tiles, {img.size}')
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            for attempt in range(3):
                try:
                    img.paste(fetch(ZOOM, tx, ty), ((tx - tx0) * TILE, (ty - ty0) * TILE)); break
                except Exception as e:
                    print('  retry', tx, ty, e); time.sleep(2)
            time.sleep(0.05)
    img.save(OUT / 'okoli.jpg', 'JPEG', quality=78, optimize=True, progressive=True)
    meta = {'image': 'assets/map/okoli.jpg', 'zoom': ZOOM, 'tx0': tx0, 'ty0': ty0, 'w': img.width, 'h': img.height, 'tile': TILE,
            'attribution': '© přispěvatelé OpenStreetMap'}
    (ROOT / 'data' / 'map.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ok', OUT / 'okoli.jpg', (OUT / 'okoli.jpg').stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
