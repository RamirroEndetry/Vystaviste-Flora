# -*- coding: utf-8 -*-
"""Stáhne fotografie z webu flora-ol.cz (parky, skleníky, pavilony, akce) a uloží je zmenšené do assets/photos.
Usage: python -X utf8 scripts/fetch-assets.py            # stáhne chybějící
       python -X utf8 scripts/fetch-assets.py --force    # přepíše vše
Fotografie jsou majetkem Výstaviště Flora Olomouc, a.s. – před nasazením je nutný souhlas provozovatele.
"""
import io, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'photos'
MAX_W = 1200
FORCE = '--force' in sys.argv
WWW, PARKY = 'https://www.flora-ol.cz/', 'https://parky.flora-ol.cz/'

PHOTOS = {
    # areál a pavilony
    'areal-mapa': WWW + 'images/event-map.jpg',
    'pavilon-a': WWW + 'images/parks/pavilon-a.jpg',
    'pavilony-male': WWW + 'images/premises/pavilon-small/pavilon-1_thumb.jpg',
    'oranzerie': WWW + 'images/premises/orangery/orangerie-4_thumb.jpg',
    'plochy-samba': WWW + 'images/premises/paved-areas/paved-8_thumb.jpg',
    'skleniky-exterier': WWW + 'images/premises/greenhouses/sklenik-2_thumb.jpg',
    'smetanovy-sady-letecky': WWW + 'images/parks/smetanovy-sady.jpg',
    # parky
    'smetanovy-sady': PARKY + 'images/smetanovy-sady.jpg',
    'smetanovy-sady-hero': PARKY + 'jpeg-images-crop/1150x500/page/54/dji-0244.JPG',
    'bezrucovy-sady': PARKY + 'images/bezrucovy-sady.jpg',
    'bezrucovy-vodopad': PARKY + 'jpeg-images-crop/1150x500/page/56/vodopad-21.jpg',
    'bezrucovy-1': PARKY + 'uploads/page/56/pic/bezruueovy-sady-foto-novz-web-1.jpg',
    'cechovy-sady': PARKY + 'images/cechovy-sady.jpg',
    'cechovy-hero': PARKY + 'jpeg-images-crop/1150x500/page/55/img-20220103-114734.jpg',
    'botanicka-rozarium': PARKY + 'images/botanicka-zahrada-a-rozarium.jpg',
    'botanicka-hero': PARKY + 'jpeg-images-crop/1150x500/page/58/14.JPG',
    'botanicka-1': PARKY + 'uploads/page/58/pic/9.jpg',
    'botanicka-2': PARKY + 'uploads/page/58/pic/5-1.JPG',
    'rozarium': PARKY + 'images/rozarium.jpg',
    'rozarium-hero': PARKY + 'jpeg-images-crop/1150x500/page/59/19.jpg',
    'skleniky': PARKY + 'images/sbirkove-skleniky.jpg',
    'skleniky-hero': PARKY + 'jpeg-images-crop/1150x500/page/60/12.jpg',
    'skleniky-1': PARKY + 'uploads/page/60/pic/img-0301.jpg',
    'skleniky-2': PARKY + 'uploads/page/60/pic/dsc-6939.jpg',
    'skleniky-3': PARKY + 'uploads/page/60/pic/mg-7125.jpg',
    'skleniky-4': PARKY + 'uploads/page/60/pic/1.jpg',
    'skleniky-5': PARKY + 'uploads/page/60/pic/5.jpg',
    'skleniky-6': PARKY + 'uploads/page/60/pic/img-0332.jpg',
    'skleniky-7': PARKY + 'uploads/page/60/pic/dsc09308.jpg',
    'park-pod-domem': PARKY + 'images/park-pod-domem.jpg',
    'aso-park': PARKY + 'images/aso-park.jpg',
    # akce 2026
    'ev-stavotech-2026': WWW + 'jpeg-images-crop/756x480/event/671/stavotech.jpeg',
    'ev-udrzitelne-vanoce-2026': WWW + 'jpeg-images-crop/756x480/event/672/vanoce-flora.jpg',
    'ev-rukodelne-trhy-2026': WWW + 'jpeg-images-crop/756x480/event/634/1-rukodele-trhy-olomouc-2026-web.jpg',
    'ev-flora-olomouc-2026': WWW + 'jpeg-images-crop/756x480/event/595/fo-tony-flory-web-image-756x480-01.jpg',
    'ev-hortikomplex-2026': WWW + 'jpeg-images-crop/756x480/event/597/web-nahled.jpg',
    'ev-tommy-emmanuel': WWW + 'jpeg-images-crop/756x480/event/670/tommy-emanuel-web.jpg',
    'ev-maker-faire-2026': WWW + 'jpeg-images-crop/756x480/event/669/makerfair-web.jpg',
    'ev-smokie': WWW + 'jpeg-images-crop/756x480/event/637/smokie-poster-2022-2-square-no-text.jpg',
    'ev-svet-kostek-2026': WWW + 'jpeg-images-crop/756x480/event/598/web.jpg',
    'ev-klenoty-pralesa-2026': WWW + 'jpeg-images-crop/756x480/event/601/kp-web.jpg',
    'ev-vyznani-ruzim-2026': WWW + 'jpeg-images-crop/756x480/event/600/web-nahled.jpg',
    'ev-zive-pasti-2026': WWW + 'jpeg-images-crop/756x480/event/599/web-nahled.jpg',
    # galerie výstav
    'flora-1': WWW + 'uploads/event/595/pic/oranzerie-pavilon-a-20.jpg',
    'flora-2': WWW + 'uploads/event/595/pic/sobota-53.jpg',
    'flora-3': WWW + 'uploads/event/595/pic/sobota-27.jpg',
    'flora-4': WWW + 'uploads/event/595/pic/02-sobota-21.jpg',
    'flora-5': WWW + 'uploads/event/595/pic/bonsaje-pavilon-e-jf-24-6.jpg',
    'horti-1': WWW + 'uploads/event/597/pic/pavilon-a-oranzerie-20.jpg',
    'horti-2': WWW + 'uploads/event/597/pic/sobota1-25.jpg',
    'horti-3': WWW + 'uploads/event/597/pic/pavilon-a-oranzerie-50.jpg',
    'horti-4': WWW + 'uploads/event/597/pic/sobota1-50.jpg',
    'horti-5': WWW + 'uploads/event/597/pic/dany7206-fotoschulz.JPG',
    'horti-6': WWW + 'uploads/event/597/pic/dany7399-fotoschulz.JPG',
    'kostky-1': WWW + 'uploads/event/598/pic/sk-a4.jpg',
    'kostky-2': WWW + 'uploads/event/598/pic/img-3765.JPG',
    'kostky-3': WWW + 'uploads/event/598/pic/073a0499.jpg',
    'klenoty-1': WWW + 'uploads/event/601/pic/img-1777.jpeg',
    'klenoty-2': WWW + 'uploads/event/601/pic/img-9123.JPG',
    'ruze-1': WWW + 'uploads/event/600/pic/vytaniruziciste-origo-47.jpg',
    'ruze-2': WWW + 'uploads/event/600/pic/vytaniruziciste-origo-10.jpg',
    'ruze-3': WWW + 'uploads/event/600/pic/02-vyzvani-ruzim-2024-28.jpg',
    'pasti-1': WWW + 'uploads/event/599/pic/img-20240524-111019.jpg',
}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (vystaviste-flora-app prototype)'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in PHOTOS.items():
        dest = OUT / f'{name}.jpg'
        if dest.exists() and not FORCE:
            continue
        try:
            im = Image.open(io.BytesIO(fetch(url)))
        except Exception as e:
            print('FAIL', name, e); continue
        im = ImageOps.exif_transpose(im).convert('RGB')
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
        im.save(dest, 'JPEG', quality=80, optimize=True, progressive=True)
        print('ok', dest.name, im.size, dest.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
