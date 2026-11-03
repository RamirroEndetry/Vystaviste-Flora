# Výstaviště Flora Olomouc – průvodce (prototyp)

Webová aplikace pro návštěvníky **Výstaviště Flora Olomouc** (Wolkerova 37/17, Olomouc) – akce a výstavy, sbírkové skleníky, rozárium, botanická zahrada, historické parky, vstupenky, doprava a parkování. Mobil-first, instalovatelná jako PWA, funguje i bez signálu, s dotykovou klávesnicí a video spořičem pro infopanely. Postaveno na stejném základu jako aplikace pro OC Flora (sousední složka `../OC Flóra`).

| Obrazovka | Co umí |
|---|---|
| **Dnes** | Pozdrav, co se dnes koná / nejbližší akce, stavová lišta (skleníky, rozárium, botanická zahrada, food park – otevřeno/zavřeno teď), rychlé dlaždice, chystané akce, Můj program, aktuality. |
| **Akce** | 42 akcí roku 2026 (probíhá / chystá se / proběhlo), filtr podle typu, hledání, měsíční seskupení. Detail: termín, hodiny po dnech, vstupné (na místě / online), popis, pořadatel, fotografie, místo konání, parkování, odkaz na vstupenky. Tradiční roční kalendář. |
| **Parky** | Sbírkové skleníky (4 expozice, sezónní otevírací doba, vstupné), rozárium, botanická zahrada, Smetanovy, Bezručovy a Čechovy sady, Park pod Dómem, ASO park – se stavem „otevřeno do…“ podle měsíce, dne v týdnu i svátků. |
| **Areál** | Mapa okolí v aplikaci (OSM), pavilon A, pavilony B/C, E/G/H, oranžerie, Samba a pódia, Food park (provozovny a hodiny), restaurace, Olomoucká tržnice (St a So 7–12). |
| **Více** | Vstupenky, dárkové poukazy a VIP karta, doprava (tramvaje 1/4/6, autobusy 16/17/28/51, vlak, zájezdové autobusy), parkování (P6 Šantovka zdarma při akcích + poznámka „kde stojím“), kontakt, aktuality, vzhled, klávesnice, spořič, instalace. |

Vše osobní (Můj program, parkování) zůstává jen v zařízení (`localStorage`, klíč `vfo-app-v1`).

## Živá verze

https://ramirroendetry.github.io/Vystaviste-Flora/ (GitHub Pages z větve `main`, repozitář https://github.com/RamirroEndetry/Vystaviste-Flora).

## Spuštění

```bash
python -X utf8 scripts/serve.py 5181
```

Poté otevřete http://localhost:5181/ (service worker vyžaduje http/https). Server podporuje HTTP Range kvůli videu spořiče. V aplikaci Claude lze použít `.claude/launch.json` (konfigurace `vystaviste-app`).

### Testování s jiným časem

Stavy (probíhající výstava, zimní hodiny skleníků, svátek) lze ověřit parametrem `?now=`, např. `index.html?now=2026-11-06T10:30#/dnes` (probíhá Stavotech) nebo `?now=2026-07-04T11:00#/misto/rozarium` (letní sezóna). Simulace se drží po dobu karty, v záhlaví svítí žlutý štítek **TEST**; zrušíte ji v **Více → Simulovaný čas → Zrušit**.

## Režim infopanelu (uzavřená aplikace)

Na širokých obrazovkách (od 900 px – infopanely, stejně jako dotyková klávesnice) se režim infopanelu zapíná **automaticky**, na mobilech zůstává vypnutý. Ručně ho přebijete adresou `index.html?kiosk=on` nebo `?kiosk=off` (uloží se v zařízení; `?kiosk=auto` vrátí automatiku; v aplikaci žádné tlačítko k vypnutí není). V tomto režimu aplikace nikdy neopustí svou stránku:

- **Odkazy ven** (web akce, Ticketportal, Google Maps, sociální sítě, flora-ol.cz…) se neotevřou – místo toho vyjede panel s **QR kódem** a adresou, návštěvník si ji načte vlastním telefonem. Panel se sám zavře po minutě.
- **Telefony a e-maily** se zobrazí stejně: jako QR kód s kontaktem k uložení do mobilu.
- **Navigace** používá vlastní **mapu okolí** (`#/mapa`), která je uložená v aplikaci: dlaždice OpenStreetMap kolem výstaviště, parků, rozária, zastávek a parkovišť. Mapa ukazuje „Jste zde“ (poloha panelu – nastavíte ve **Více → Poloha tohoto panelu** nebo adresou `?kde=skleniky`), cíl, vzdálenost, směr a odhad chůze. Funguje i bez internetu.
- Dlouhý stisk / pravé tlačítko a přibližování stránky jsou potlačené, nabídka instalace je skrytá.

Mapu vygeneruje `python -X utf8 scripts/make-map.py` (stáhne cca 170 dlaždic OSM do `assets/map/okoli.jpg` a zapíše `data/map.json`, ze kterého `build-data.py` doplní polohy). Souřadnice míst pocházejí z OpenStreetMap (Overpass).

Samotný prohlížeč na panelu spusťte v kiosk režimu (např. Chrome `--kiosk --incognito "https://…/index.html?kiosk=on&kde=pavilon-a"`), aby nešlo otevřít adresní řádek ani jiné aplikace – to už aplikace sama zajistit nemůže.

## Dotyková klávesnice a spořič

`keyboard.js` – klávesnice pro infopanely (QWERTZ bez diakritiky), režim ve **Více → Dotyková klávesnice** nebo `?klavesnice=on|off|auto`.

`assets/intro/intro.mp4` (1920×1080) a `intro-portrait.mp4` (1080×1920) je 30s smyčka: originální logo Výstaviště Flora Olomouc, výstavy Flora Olomouc, sbírkové skleníky, rozárium a parky, chystané akce (plakáty), doprava (tramvaje 1/4/6, P6 Šantovka) a závěrečné „Vítejte“. `screensaver.js` ji přehraje při otevření a po 30 s nečinnosti; na výšku se použije svislá verze (`?video=vyska` / `?video=sirka`). Ručně: **Více → Spořič obrazovky → Přehrát**.

```bash
python -X utf8 scripts/render-intro.py
python -X utf8 scripts/render-intro.py --portrait
python -X utf8 scripts/render-intro.py --preview 2.8 7 12 16.5 21 25.5 28.9 --out <složka>
```

(Pillow + numpy + ffmpeg; texty a časování scén jsou nahoře ve skriptu.)

## Logo, ikony a fotografie

Originální logo je SVG symbol z webu flora-ol.cz (`assets/logo/logo-vystaviste-flora.svg` – znak i nápis, `logo-znak.svg` – samotný znak). `python -X utf8 scripts/make-icons.py` z něj vyrobí bílé/zelené varianty pro záhlaví a ikony PWA. `python -X utf8 scripts/fetch-assets.py` stáhne a zmenší fotografie z flora-ol.cz do `assets/photos/` (seznam je ve skriptu).

## Data

`scripts/build-data.py` obsahuje všechny údaje (místa, sezónní otevírací doby, vstupné, akce 2026 s hodinami a cenami, doprava, parkování, vstupenky, aktuality) ručně přepsané z webů flora-ol.cz, akce.flora-ol.cz a parky.flora-ol.cz ke dni 3. 11. 2026 a generuje `data.js`:

```bash
python -X utf8 scripts/build-data.py
```

Otevírací doby jsou pravidla po měsících a dnech v týdnu (`rules`), s výjimkami pro konkrétní dny (`overrides`, `holidaysOpen`) – aplikace z nich počítá stav pro libovolné datum.

## Omezení prototypu

- Data jsou statický snímek; termíny roku 2027 web zatím neuvádí (aplikace zobrazuje jen tradiční roční kalendář).
- GPS souřadnice míst jsou přibližné (adresa sídla ověřena přes OpenStreetMap, ostatní odhad) – slouží pro navigaci v okolí.
- Otevírací doba restaurací Fontána a áčko není na webu uvedena.
- Není to oficiální aplikace Výstaviště Flora Olomouc; fotografie a logo jsou majetkem společnosti – před nasazením je nutný souhlas provozovatele.
