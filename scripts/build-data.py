# -*- coding: utf-8 -*-
"""Sestaví data.js pro aplikaci Výstaviště Flora Olomouc.
Údaje byly ručně přepsány z webů flora-ol.cz, akce.flora-ol.cz a parky.flora-ol.cz (stav k datu UPDATED níže).
Usage: python -X utf8 scripts/build-data.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPDATED = '2026-11-03'
PH = 'assets/photos/'


def t(s):
    """'9:00' -> minuty od půlnoci"""
    h, m = s.split(':'); return int(h) * 60 + int(m)


def rule(months, days, o, c, **kw):
    """Sezónní pravidlo otevírací doby: měsíce (1–12), dny (1=Po … 7=Ne), od–do."""
    r = {'m': months, 'd': days, 'o': t(o), 'c': t(c)}; r.update(kw); return r


ALL = [1, 2, 3, 4, 5, 6, 7]
WEEKDAYS = [1, 2, 3, 4, 5]
WEEKEND = [6, 7]
# standardní sezóna rozária a botanické zahrady (shodná)
GARDEN_RULES = [
    rule([4, 5], ALL, '9:00', '18:00'), rule([6, 7, 8], ALL, '9:00', '19:00'), rule([9], ALL, '9:00', '18:00'),
    rule([10], ALL, '9:00', '17:00'), rule([11, 12, 1, 2, 3], WEEKDAYS, '8:00', '15:00', hol='closed', note='jen venkovní prostor, infocentrum zavřené'),
]
GARDEN_PRICES = [{'label': 'Vstup', 'onsite': 0, 'free': True}, {'label': 'Průvodce (60 min, objednat předem)', 'onsite': 400}, {'label': 'Grilování (rezervace na infocentru)', 'onsite': 300}, {'label': 'Fotografování pro soukromé účely', 'onsite': 0, 'free': True}]
GREENHOUSE_PRICES = [
    {'label': 'Plné vstupné', 'onsite': 100}, {'label': 'Děti 6–15 let', 'onsite': 50}, {'label': 'Studenti, senioři 65+, ZTP, ZTP/P', 'onsite': 60},
    {'label': 'Rodinné (2 dospělí + až 3 děti do 15 let)', 'onsite': 280}, {'label': 'Děti do 6 let s dospělým, doprovod ZTP/P', 'onsite': 0, 'free': True}, {'label': 'Celoroční permanentka', 'onsite': 700},
]
FLORA_PRICES = [
    {'label': 'Plné vstupné', 'onsite': 220, 'online': 200}, {'label': 'Studenti 15–26 let', 'onsite': 140, 'online': 130}, {'label': 'Senioři 65+', 'onsite': 140, 'online': 130},
    {'label': 'Děti 6–15 let', 'onsite': 110, 'online': 100}, {'label': 'ZTP, ZTP/P (doprovod zdarma)', 'onsite': 110, 'online': 100}, {'label': 'Rodinné (2 dospělí + 3 děti)', 'onsite': 490, 'online': 460},
    {'label': 'Školní skupiny (nad 10 osob)', 'onsite': 90, 'online': 90}, {'label': 'Děti do 6 let', 'onsite': 0, 'free': True},
]
SKLENIK_EVENT_PRICES = [
    {'label': 'Plné vstupné', 'onsite': 150, 'online': 130}, {'label': 'Studenti 15–26, senioři 65+', 'onsite': 90, 'online': 80}, {'label': 'Děti 6–15, ZTP, ZTP/P', 'onsite': 80, 'online': 70},
    {'label': 'Rodinné (2 dospělí + až 3 děti)', 'onsite': 350, 'online': 320}, {'label': 'Děti do 6 let', 'onsite': 0, 'free': True},
]

center = {
    'name': 'Výstaviště Flora Olomouc', 'short': 'Flora Olomouc', 'company': 'Výstaviště Flora Olomouc, a.s.',
    'address': 'Wolkerova 37/17, 779 00 Olomouc', 'gps': [49.5886, 17.24511], 'phone': '+420 585 726 111', 'email': 'sekretariat@flora-ol.cz',
    'ico': '25848526', 'datovka': 'ictcikd', 'web': 'https://www.flora-ol.cz/',
    'tickets': {'phone': '+420 585 726 232', 'email': 'vstupenky@flora-ol.cz', 'online': 'https://akce.flora-ol.cz/vstupenky', 'person': 'Alena Nádvorníková (pokladní, hromadné objednávky)'},
    'social': {'facebook': 'https://www.facebook.com/FloraOlomouc/', 'instagram': 'https://www.instagram.com/flora_ol/', 'youtube': 'https://www.youtube.com/@vystavistefloraolomouc5230'},
    'facts': [
        'Více než 60 let tradice výstavnictví v Olomouci',
        'Flora Olomouc – největší a nejstarší květinová výstava v Česku (od roku 1958 ... ověřit: web uvádí „více než 50 let tradice“)',
        'Sbírkové skleníky: 4 100 m², palmový skleník z roku 1927 je kulturní památkou',
        'Rozárium: přes 4 500 keřů růží, druhé největší v ČR, Národní sbírka rostlin',
        'Společnost pečuje o cca 50 ha historických parků v centru Olomouce',
    ],
}
# „ověřit“ v textu výše je jen interní poznámka – odstraníme a ponecháme ověřené znění
center['facts'][1] = 'Flora Olomouc – největší a nejstarší květinová výstava v Česku, přes 50 let tradice'

# ---------------------------------------------------------------------------------------------------------------
# Místa: areál výstaviště, parky, zahrady, skleníky, gastro, tržnice
# ---------------------------------------------------------------------------------------------------------------
places = [
    # --- areál výstaviště ---
    {'id': 'pavilon-a', 'kind': 'pavilon', 'name': 'Pavilon A', 'short': 'Hlavní výstavní pavilon', 'image': PH + 'pavilon-a.jpg',
     'desc': 'Největší pavilon výstaviště: 60 × 42 m na dvou podlažích, klimatizovaný, multifunkční a bezbariérový. Po rekonstrukci v roce 2016 má výtah, eskalátory, bufet a pokladny. Hostí hlavní expozice výstav Flora Olomouc, veletrhy, koncerty i plesy. Zastávka tramvaje „Výstaviště Flora“ je přímo před vstupem.',
     'facts': ['60 × 42 m, 2 podlaží', 'Klimatizace, výtah, eskalátory', 'Bufet a pokladny', 'Bezbariérový přístup'], 'gps': [49.58835, 17.24534]},
    {'id': 'pavilony-e-g-h', 'kind': 'pavilon', 'name': 'Pavilony E, G a H', 'short': 'Menší pavilony v parku', 'image': PH + 'pavilony-male.jpg',
     'desc': 'Tři menší pavilony v parkové části Smetanových sadů. Slouží jako kryté prodejní plochy a pro menší akce – soutěže, závody, školení, výstavy a dětské programy. Při výstavách Flora Olomouc tu bývají regionální potraviny (E), doprovodné trhy (G) a výstavy bonsají či včelařství (H).',
     'facts': ['Kryté prodejní plochy', 'Menší akce a workshopy'], 'gps': [49.58753, 17.24687]},
    {'id': 'pavilony-b-c', 'kind': 'pavilon', 'name': 'Pavilony B a C', 'short': 'Galerie a workshopy u pavilonu A', 'image': PH + 'flora-1.jpg',
     'desc': 'Navazují na pavilon A. Při výstavách tu bývá prezentace Svazu květinářů a floristů (B, přízemí) a zahradnických škol s floristickými workshopy (C, 1. patro).',
     'facts': ['Přízemí a 1. patro', 'Floristické soutěže a workshopy'], 'gps': [49.5882, 17.246]},
    {'id': 'oranzerie', 'kind': 'pavilon', 'name': 'Oranžerie', 'short': 'Zdobná stavba s atmosférou 19. století', 'image': PH + 'oranzerie.jpg',
     'desc': 'Zdobná budova s dřevořezbami inspirovaná oranžerií ve Versailles – vysoká okna a atmosféra 19. století. Při výstavách hostí komorní expozice (např. „Rozkvetlá partitura“, dýně a nástroje našich předků), jinak svatby, konference a fotografování.',
     'facts': ['Inspirace Versailles', 'Svatby a komorní výstavy'], 'gps': [49.5877, 17.2481]},
    {'id': 'samba', 'kind': 'pavilon', 'name': 'Areál Samba, Letní scéna a Hudební pavilon', 'short': 'Venkovní zpevněné plochy a pódia', 'image': PH + 'plochy-samba.jpg',
     'desc': 'Venkovní plochy s elektropřípojkami pro trhy, stánky, pódia a festivaly. Pódium SAMBA hostí při výstavách hudební a rozhlasové programy, soutěže ve vyřezávání dýní i dětský program. Hudební pavilon stojí v Rudolfově aleji naproti restauraci Fontána.',
     'facts': ['Trhy a festivaly', 'Pódium SAMBA', 'Hudební pavilon v Rudolfově aleji'], 'gps': [49.587, 17.2476]},
    {'id': 'food-park', 'kind': 'gastro', 'name': 'Food park Flora', 'short': 'Občerstvení mezi pavilony A a E', 'image': PH + 'plochy-samba.jpg',
     'desc': 'Jedinečný prostor na kraji Smetanových sadů mezi pavilony A a E – místo pro odpočinek, jídlo a pití po celý rok. Tři stálé provozovny: COFFEE PARK (káva, snacky, točené pivo, lokální produkty – od roku 2020), Zmrzlinárium Flora (často se měnící příchutě včetně zmrzliny FLORA) a BISTRO PARK s francouzskými palačinkami, burgery a wrapy.',
     'vendors': [
         {'name': 'COFFEE PARK', 'what': 'káva, snacky, točené pivo, lokální produkty', 'hours': 'denně 10:00–22:00', 'web': 'https://coffeepark.eu'},
         {'name': 'Zmrzlinárium Flora', 'what': 'zmrzlina s měnícími se příchutěmi', 'hours': 'denně 10:00–20:00 (za příznivého počasí)', 'web': 'https://zmrzlinarium.cz'},
         {'name': 'BISTRO PARK & francouzské palačinky', 'what': 'sladké i slané palačinky, burgery, wrapy, nápoje', 'hours': 'denně 10:00–21:00 (za příznivého počasí)', 'web': 'https://palacinkola.cz'},
     ],
     'hours': {'rules': [rule(list(range(1, 13)), ALL, '10:00', '22:00')], 'note': 'Coffee Park denně 10–22; zmrzlina do 20:00 a bistro do 21:00 jen za příznivého počasí.'},
     'facts': ['Otevřeno celoročně', 'Mezi pavilony A a E'], 'gps': [49.58755, 17.24615]},
    {'id': 'restaurace-fontana', 'kind': 'gastro', 'name': 'Restaurace Fontána', 'short': 'Bývalý lázeňský pavilon v Rudolfově aleji', 'image': PH + 'smetanovy-sady.jpg',
     'desc': 'Nejvýznamnější architektonická památka Smetanových sadů – postavena jako lázeňský pavilon. Stojí u Rudolfovy aleje naproti fontáně s vodotryskem a hudebnímu pavilonu. Restauraci provozuje externí partner; otevírací dobu a menu ověřte u provozovatele.',
     'facts': ['Rudolfova alej', 'Externí provozovatel'], 'gps': [49.58721, 17.25114]},
    {'id': 'restaurace-acko', 'kind': 'gastro', 'name': 'Restaurace áčko', 'short': 'Restaurace u pavilonu A', 'image': PH + 'pavilon-a.jpg',
     'desc': 'Restaurace v areálu výstaviště provozovaná externím partnerem. Otevírací dobu a nabídku ověřte přímo u provozovatele.',
     'facts': ['Externí provozovatel'], 'gps': [49.5885, 17.245]},
    {'id': 'trznice', 'kind': 'trznice', 'name': 'Olomoucká tržnice', 'short': 'Městská tržnice – trhy ve středu a v sobotu', 'image': PH + 'areal-mapa.jpg',
     'desc': 'Městskou tržnici spravuje Výstaviště Flora Olomouc od 1. února 2022. Od té doby zmizely staré dřevěné stánky, vzniklo květinové odpočinkové místo Green Point, truhlíky oddělují tržnici od parkoviště, betonové prodejní stoly byly opraveny a parkoviště dostalo automatickou závoru. Klasické trhy probíhají ve středu a v sobotu 7:00–12:00; v hlavní sezóně mohou prodejci prodávat i v jiné dny.',
     'hours': {'rules': [rule(list(range(1, 13)), [3, 6], '7:00', '12:00')], 'note': 'Trhy ve středu a v sobotu. V hlavní sezóně prodejci podle vlastního uvážení i jindy.'},
     'facts': ['Trhy St a So 7–12', 'Placené parkoviště se závorou', 'Odpočinkové místo Green Point'],
     'contact': 'Ing. Helena Kilianová, správkyně tržnice', 'phone': '+420 737 213 639', 'email': 'kilianova.helena@flora-ol.cz', 'gps': [49.5895, 17.255],
     'url': 'https://www.flora-ol.cz/olomoucka-trznice'},
    # --- skleníky, zahrady, parky ---
    {'id': 'skleniky', 'kind': 'sklenik', 'name': 'Sbírkové skleníky', 'short': 'Palmový, kaktusový, tropický a subtropický skleník', 'image': PH + 'skleniky-hero.jpg',
     'gallery': [PH + 'skleniky-1.jpg', PH + 'skleniky-2.jpg', PH + 'skleniky-3.jpg', PH + 'skleniky-4.jpg', PH + 'skleniky-5.jpg', PH + 'skleniky-6.jpg', PH + 'skleniky-7.jpg'],
     'desc': 'Olomoucké sbírkové skleníky ve Smetanových sadech patří k největším a nejstarším v České republice: 4 100 m², z toho přes 3 000 m² přístupných veřejnosti. Čekají tu mohutné palmy, největší leknín světa, vůně citrusů, jedny z největších kulovitých kaktusů v Evropě, exotičtí ptáci a plazi i mořské a sladkovodní akvárium.',
     'sections': [
         {'name': 'Palmový skleník', 'text': 'Jeden z největších v ČR: 73 m dlouhý, 20 m široký a 10 m vysoký, necelých 1 500 m². Stovky druhů rostlin včetně padesátky druhů palem – nejstarší má přes 150 let (datlovník kanárský, drsnoplod Fortuneův, fíkovník pryžodárný, blahočety). Žijí tu ptáci, plazi, ryby i jihoamerický kajman žakare. Skleník z roku 1927 je kulturní památkou; vstupní portál se sochami vytvořil Julius Pelikán, žák J. V. Myslbeka.'},
         {'name': 'Kaktusový skleník', 'text': 'Nejvzácnější sbírka kaktusů a sukulentů v ČR, včetně jedněch z největších kulovitých kaktusů (Echinocactus grusonii) v Evropě. Nejcennější astrofyta údajně pocházejí ze sbírky cestovatele A. V. Friče. Nejkrásnější je v červnu, kdy skleník rozzáří záplava květů.'},
         {'name': 'Tropický skleník', 'text': 'Největší leknín světa viktorie Cruzova s až dvoumetrovými plovoucími listy – její bílý květ je k vidění jen pár hodin jediného dne. Vonné liány, bromélie, orchideje, tilandsie a oblíbený bílý sumec.'},
         {'name': 'Subtropický (citrusový) skleník', 'text': 'Středomořská zahrada plná vůní: pomeranče, mandarinky, citrony, grapefruity, tomely, fíky, olivy, granátová jablka, rohovník i kiwi a masožravé rostliny.'},
     ],
     'hours': {'rules': [
         rule([1], [], '0:00', '0:00', closed=True, note='v lednu zavřeno'),
         rule([2, 11, 12], WEEKEND, '9:00', '16:00', start='2026-02-07', end='2026-12-13'),
         rule([3], [2, 3, 4, 5, 6, 7], '9:00', '17:00'),
         rule([4, 5, 6, 7, 8, 9, 10], [2, 3, 4, 5, 6, 7], '9:00', '18:00'),
     ], 'holidaysOpen': ['2026-04-03', '2026-04-06', '2026-05-01', '2026-05-08', '2026-07-05', '2026-07-06', '2026-09-28', '2026-10-28', '2026-11-17'],
         'overrides': {'2026-10-09': [t('9:00'), t('17:00')], '2026-10-10': [t('9:00'), t('17:00')], '2026-10-11': [t('9:00'), t('16:00')]},
         'note': 'Pondělí zavřeno (mimo svátky uvedené výše). Během výstavy Hortikomplex vstup zdarma v době výstavy.'},
     'prices': GREENHOUSE_PRICES, 'dogs': False,
     'contact': 'Ing. Pavel Souček, vedoucí sbírkových skleníků', 'phone': '+420 585 726 243', 'email': 'skleniky@flora-ol.cz', 'phone2': 'Pokladna skleníků +420 585 726 265',
     'address': 'Smetanovy sady, Olomouc', 'gps': [49.58701, 17.24981], 'url': 'https://parky.flora-ol.cz/sbirkove-skleniky-olomouc',
     'facts': ['4 100 m², přes 3 000 m² pro veřejnost', 'Palmový skleník 1927 – kulturní památka', 'Viktorie Cruzova – největší leknín světa', 'Kajman, exotičtí ptáci, akvária']},
    {'id': 'rozarium', 'kind': 'zahrada', 'free': True, 'name': 'Rozárium Olomouc', 'short': 'Přes 4 500 keřů růží na 3,5 ha', 'image': PH + 'rozarium-hero.jpg',
     'gallery': [PH + 'rozarium.jpg', PH + 'ruze-1.jpg', PH + 'ruze-2.jpg', PH + 'ruze-3.jpg'],
     'desc': 'Nedávno zrekonstruované rozárium na třídě 17. listopadu: přes čtyři a půl tisíce keřů růží více než tisíce domácích i světových odrůd, rozloha 3,5 hektaru. Druhé největší rozárium v ČR, jeho sbírka nese označení Národní sbírka rostlin. Založeno 1972 podle plánů architekta Emila Zavadila (záhony evokující plující ledové kry), rekonstrukci navrhl Zdeněk Sendler (1. etapa 2016). Nejkrásnější je v červnu – hlavní období kvetení, kdy se tu koná festival Vyznání růžím. Velký samoobslužný gril, svatby u vodních ploch a dřevěného mola, občerstvení Coffee Park.',
     'hours': {'rules': GARDEN_RULES, 'note': 'Vstup ze tř. 17. listopadu nebo přes botanickou zahradu z Bezručových sadů. Od listopadu do března jen venkovní prostor; o svátcích a za nepříznivého počasí zavřeno.'},
     'prices': GARDEN_PRICES, 'dogs': False,
     'contact': 'Jiří Malaska, vedoucí botanické zahrady a rozária', 'phone': '+420 585 225 566', 'email': 'botanicka@flora-ol.cz', 'phone2': 'Infocentrum rozária (komentované prohlídky, grilování) +420 739 322 603',
     'address': 'třída 17. listopadu, Olomouc', 'gps': [49.5923, 17.26124], 'url': 'https://parky.flora-ol.cz/rozarium-olomouc',
     'facts': ['4 500+ keřů růží, 1 000+ odrůd', '3,5 ha, založeno 1972', 'Národní sbírka rostlin', 'Gril, svatby, Coffee Park']},
    {'id': 'botanicka', 'kind': 'zahrada', 'free': True, 'name': 'Botanická zahrada Olomouc', 'short': 'Zelená oáza u Bezručových sadů', 'image': PH + 'botanicka-hero.jpg',
     'gallery': [PH + 'botanicka-rozarium.jpg', PH + 'botanicka-1.jpg', PH + 'botanicka-2.jpg'],
     'desc': 'Unikátní zelená oáza na 3,5 ha na ploše bývalé Korunní pevnůstky, připojená k parkům v 60. letech 20. století. Zahrada smyslů pro zrakově hendikepované (80 druhů bylin, popisky v Braillově písmu, autor Ivar Otruba), jarní expozice hájové květeny na břehu Mlýnského potoka (sněženky, bledule, dymnivky, sasanky, česnek medvědí), 40 m dlouhý záhon s 50 odrůdami lilií, dětské hřiště ve stínu stromů, naučné hry Malý botanik a Nej… ze světa rostlin (50 Kč na infocentru rozária) a samoobslužný gril.',
     'hours': {'rules': GARDEN_RULES, 'note': 'Vstup z Bezručových sadů nebo z rozária (tř. 17. listopadu). Od listopadu do března jen venkovní prostor; o svátcích a za nepříznivého počasí zavřeno.'},
     'prices': GARDEN_PRICES, 'dogs': False,
     'contact': 'Jiří Malaska, vedoucí botanické zahrady a rozária', 'phone': '+420 585 225 566', 'email': 'botanicka@flora-ol.cz',
     'address': 'u Bezručových sadů / tř. 17. listopadu, Olomouc', 'gps': [49.5927, 17.25952], 'url': 'https://www.flora-ol.cz/botanicka-zahrada-olomouc',
     'facts': ['3,5 ha', 'Zahrada smyslů', 'Hřiště a naučné hry pro děti', 'Expozice lilií a hájové květeny']},
    {'id': 'smetanovy-sady', 'kind': 'park', 'name': 'Smetanovy sady', 'short': 'Nejstarší a největší park Olomouce, 19 ha', 'image': PH + 'smetanovy-sady-hero.jpg',
     'gallery': [PH + 'smetanovy-sady.jpg', PH + 'smetanovy-sady-letecky.jpg'],
     'desc': 'Nejstarší a největší olomoucký park (cca 19 ha) na západním obvodu centra, kulturní památka. Páteří je 710 m dlouhá Rudolfova alej – promenáda s proslulými ornamentálními a trvalkovými záhony, založená 1800 arcibiskupem Rudolfem Janem Habsburským a obnovená 1866. Najdete tu restauraci Fontána (bývalý lázeňský pavilon), fontánu s vodotryskem, hudební pavilon, Magnoliovou zahradu, Pinetum, Letní čítárnu, jezírko, památný 250 let starý Rudolfův dub, sbírkové skleníky a pavilony výstaviště. Nadzemní chodníky park spojují přes Wolkerovu ulici s Čechovými sady.',
     'hours': {'always': True, 'note': 'Městské parky jsou otevřeny celoročně, vstup zdarma.'}, 'free': True,
     'address': 'Olomouc – západní obvod centra', 'gps': [49.58819, 17.25011], 'url': 'https://parky.flora-ol.cz/smetanovy-sady',
     'facts': ['cca 19 ha, kulturní památka', 'Rudolfova alej 710 m', 'Rudolfův dub – 250 let', 'Sbírkové skleníky, Fontána, hudební pavilon']},
    {'id': 'bezrucovy-sady', 'kind': 'park', 'name': 'Bezručovy sady', 'short': 'Park pod hradbami s umělým vodopádem, 11,5 ha', 'image': PH + 'bezrucovy-vodopad.jpg',
     'gallery': [PH + 'bezrucovy-sady.jpg', PH + 'bezrucovy-1.jpg'],
     'desc': 'Park z roku 1898 pod středověkými a tereziánskými hradbami, dnes téměř 11,5 ha, kulturní památka. Ohraničuje ho skalnatý břeh Mlýnského potoka. Symbolem je umělý vodopád z roku 1965 (postavil podnik Sigma Olomouc), obnovený na jaře 2022 – v provozu od jara do podzimu ve všední dny 13–18 h a o víkendech 10–18 h. Dále Jugoslávské mauzoleum (1926), zvonička u Katových schodů a památník Petra Bezruče (1947). Na levém břehu potoka navazuje botanická zahrada a rozárium.',
     'hours': {'always': True, 'note': 'Otevřeno celoročně, vstup zdarma. Vodopád: jaro–podzim, Po–Pá 13:00–18:00, So–Ne 10:00–18:00.'}, 'free': True,
     'address': 'Olomouc – pod hradbami, u kostela sv. Michala', 'gps': [49.59251, 17.25867], 'url': 'https://parky.flora-ol.cz/bezrucovy-sady',
     'facts': ['11,5 ha, od roku 1898', 'Umělý vodopád (1965, obnoven 2022)', 'Jugoslávské mauzoleum', 'Navazuje botanická zahrada']},
    {'id': 'cechovy-sady', 'kind': 'park', 'name': 'Čechovy sady', 'short': 'Park s Jánským stromořadím, necelých 8 ha', 'image': PH + 'cechovy-hero.jpg',
     'gallery': [PH + 'cechovy-sady.jpg'],
     'desc': 'Park z 30. let 19. století (necelých 8 ha) v přírodně krajinářském stylu podle Maxe Machánka. Jádrem je čtyřřadé Jánské stromořadí, které spojovalo Litovelské předměstí s Terezskou bránou. Najdete tu Litovelskou bránu (přenesena 1896), pomník Karla Wellnera (1936), památník osvobození (1945) a sochu Boženy Němcové (1965). Nadzemními chodníky je park propojen se Smetanovými sady.',
     'hours': {'always': True, 'note': 'Otevřeno celoročně, vstup zdarma.'}, 'free': True,
     'address': 'Olomouc – mezi Litovelským předměstím a centrem', 'gps': [49.5929, 17.24499], 'url': 'https://parky.flora-ol.cz/cechovy-sady',
     'facts': ['necelých 8 ha, od 30. let 19. stol.', 'Jánské stromořadí', 'Litovelská brána']},
    {'id': 'park-pod-domem', 'kind': 'park', 'name': 'Park pod Dómem', 'short': 'Zeleň pod katedrálou sv. Václava', 'image': PH + 'park-pod-domem.jpg',
     'desc': 'Menší parková plocha pod katedrálou sv. Václava, kterou spolu s historickými parky udržuje Výstaviště Flora Olomouc pro město.',
     'hours': {'always': True, 'note': 'Otevřeno celoročně, vstup zdarma.'}, 'free': True, 'gps': [49.59832, 17.2596], 'url': 'https://parky.flora-ol.cz/park-pod-domem', 'facts': ['Pod katedrálou sv. Václava']},
    {'id': 'aso-park', 'kind': 'park', 'name': 'ASO park (park Na Střelnici)', 'short': 'Park u Mlýnského potoka', 'image': PH + 'aso-park.jpg',
     'desc': 'Park Na Střelnici (ASO park) u Mlýnského potoka, součást zeleně ve správě Výstaviště Flora Olomouc.',
     'hours': {'always': True, 'note': 'Otevřeno celoročně, vstup zdarma.'}, 'free': True, 'gps': [49.59942, 17.25], 'url': 'https://parky.flora-ol.cz/park-na-strelnici-aso-park', 'facts': ['U Mlýnského potoka']},
]

# ---------------------------------------------------------------------------------------------------------------
# Akce (akce.flora-ol.cz) – rok 2026. Hodiny v minutách: default + výjimky pro konkrétní dny.
# ---------------------------------------------------------------------------------------------------------------
AK = 'https://akce.flora-ol.cz/'


def ev(id, title, start, end, cat, venue, **kw):
    e = {'id': id, 'title': title, 'start': start, 'end': end or start, 'cat': cat, 'venue': venue, 'url': AK + id}
    e.update(kw); return e


def hrs(default, **days):
    h = {'default': [t(default[0]), t(default[1])]}
    for d, v in days.items(): h[d.replace('_', '-')] = [t(v[0]), t(v[1])]
    return h


events = [
    # --- chystá se / probíhá (listopad–prosinec 2026) ---
    ev('stavotech-2026', 'Stavotech 2026 – Moderní dům Olomouc', '2026-11-05', '2026-11-07', 'veletrh', 'pavilon-a', external=True, organizer='OMNIS Olomouc, a.s.',
       image=PH + 'ev-stavotech-2026.jpg', hours=hrs(('9:00', '18:00'), **{'2026_11_07': ('9:00', '17:00')}),
       prices=[{'label': 'Plné', 'onsite': 70}, {'label': 'Zlevněné', 'onsite': 40}],
       text='68. pokračování stavebního a technického veletrhu: moderní stavění, architektura, dřevostavby, úsporné vytápění, přehlídka architektury a doprovodný program. Pro všechny, kdo plánují stavbu či rekonstrukci nebo hledají nápady pro svůj dům.',
       web='https://www.omnis.cz/akce/stavotech-moderni-dum-olomouc-245/'),
    ev('tommy-emmanuel', 'Tommy Emmanuel – koncert', '2026-11-12', None, 'koncert', 'pavilon-a', external=True, image=PH + 'ev-tommy-emmanuel.jpg',
       time='19:00', doors='17:30', tickets='https://www.ticketportal.cz/event/TOMMY-EMMANUEL?idp=120022109',
       text='Australský kytarový virtuos Tommy Emmanuel sólově, se speciálním hostem – chorvatským kytaristou a skladatelem Frano Livingstonem. Vstupenky prodává Ticketportal, cenu určuje pořadatel.'),
    ev('maker-faire-olomouc-2026', 'Maker Faire Olomouc 2026', '2026-11-15', None, 'festival', 'pavilon-a', external=True, image=PH + 'ev-maker-faire-2026.jpg',
       hours=hrs(('10:00', '17:00')), tickets='https://makerfaire.cz/olomouc/vstupenky/', web='https://makerfaire.cz/olomouc/',
       text='5. ročník festivalu kreativity: makeři, vynálezci, inovátoři a kutilové. Elektronika, robotika, 3D tisk, tradiční i moderní řemesla, produktový design a udržitelné projekty – s interaktivními stanovišti pro všechny věkové kategorie. Vstupné určuje pořadatel.'),
    ev('rukodelne-trhy', 'Předvánoční rukodělné trhy 2026', '2026-11-17', None, 'trhy', 'pavilon-a', external=True, organizer='Hobby výstaviště (tel. 604 670 861)', image=PH + 'ev-rukodelne-trhy-2026.jpg',
       hours=hrs(('9:00', '18:00')), web='https://www.hobbyvystaviste.cz/',
       prices=[{'label': 'Dospělí', 'onsite': 100}, {'label': 'Senioři 65+, ZTP', 'onsite': 80}, {'label': 'Děti do 150 cm, ZTP/P + doprovod', 'onsite': 0, 'free': True}],
       text='Ručně vyráběné výrobky českých tvůrců a značek: vánoční dekorace, zdobené svíčky, šperky, keramika, dřevěné hračky, pletené a háčkované zboží, vitráže, oděvy, kosmetika. Ukázky řemesel a workshopy (zdobení baněk, výroba ozdob), sváteční jídlo a horké nápoje. Koná se o státním svátku 17. listopadu.'),
    ev('udrzitelne-vanoce-na-flore-2', 'Udržitelné Vánoce na Floře', '2026-11-28', '2026-11-29', 'trhy', 'pavilony-e-g-h', venueLabel='Pavilon E', external=True, organizer='EKO KOUTEK (za podpory Výstaviště Flora Olomouc)',
       image=PH + 'ev-udrzitelne-vanoce-2026.jpg', hours=hrs(('9:00', '17:00')),
       prices=[{'label': 'Dospělí', 'onsite': 100}, {'label': 'Děti od 6 let', 'onsite': 50}],
       text='„Dopřejte věcem další příběh.“ Vánoční radost bez nakupování nových věcí – objevte, co má ještě dlouhý život před sebou. V ceně vstupného je SWAP: cokoli užitečného si můžete odnést domů.',
       web='https://www.facebook.com/events/2516592625461990'),
    ev('smokie-uk', 'Smokie |UK| – Greatest Hits Tour', '2026-12-12', None, 'koncert', 'pavilon-a', external=True, image=PH + 'ev-smokie.jpg',
       tickets='https://www.ticketportal.cz/event/SMOKIE_UK?idp=120007307',
       text='Britská kapela Smokie se vrací do Česka. Olomoucký termín byl přidán kvůli zájmu fanoušků v rámci Greatest Hits World Tour. Začátek koncertu a ceny vstupenek určuje pořadatel (Ticketportal).'),
    # --- proběhlo 2026 (archiv) ---
    ev('svet-kostek-olomouc-2026', 'Svět kostek Olomouc 2026', '2026-10-31', '2026-11-01', 'vystava', 'pavilon-a', image=PH + 'ev-svet-kostek-2026.jpg',
       gallery=[PH + 'kostky-1.jpg', PH + 'kostky-2.jpg', PH + 'kostky-3.jpg'], hours=hrs(('9:00', '18:00'), **{'2026_11_01': ('9:00', '17:00')}), web='https://www.svet-kostek.cz/',
       prices=[{'label': 'Dospělí', 'onsite': 210, 'online': 170}, {'label': 'Senioři 65+, ZTP/ZTP-P', 'onsite': 180, 'online': 150}, {'label': 'Děti 3–15', 'onsite': 150, 'online': 120}, {'label': 'Rodinné (2+2)', 'onsite': 480, 'online': 410}, {'label': 'Děti do 3 let', 'onsite': 0, 'free': True}],
       text='Mezinárodní výstava modelů a stavebnic – stovky unikátních staveb od stavitelů ze šesti evropských zemí: 3,5 m Minas Tirith, 5 m ZOO Jasmin s 600 figurkami zvířat, nizozemský GBC kuličkový stroj, 4,7 m jeřáb, scény Star Wars a Jurassic World, RC modely, herní zóna a prodejní stánky. Parkování zdarma na P6 Galerie Šantovka.'),
    ev('klenoty-pralesa-2026', 'Klenoty pralesa 2026 – orchideje a tropické rostliny', '2026-10-16', '2026-11-01', 'vystava', 'skleniky', image=PH + 'ev-klenoty-pralesa-2026.jpg',
       gallery=[PH + 'klenoty-1.jpg', PH + 'klenoty-2.jpg'], hours=hrs(('9:00', '18:00')),
       prices=[{'label': 'Dospělí', 'onsite': 140, 'online': 130}, {'label': 'Studenti, senioři, děti 6–15, ZTP', 'onsite': 80, 'online': 70}, {'label': 'Rodinné', 'onsite': 340, 'online': 310}, {'label': 'Děti do 6 let', 'onsite': 0, 'free': True}],
       text='5. ročník prodejní výstavy orchidejí a tropických rostlin v palmovém skleníku: stovky exotických rostlin od českých i zahraničních pěstitelů, poradna kurátorky Markéty Aubrechtové Dlouhé. Phragmipedium kovachii, Nepenthes „Midnight“, orchideje Dracula, Vanda, klenotové orchideje.'),
    ev('burza-prace-a-vzdelavani', 'Burza práce a vzdělávání', '2026-10-22', None, 'veletrh', 'pavilon-a', external=True),
    ev('oslavy-lesa-na-rudolfove-aleji', 'Oslavy lesa na Rudolfově aleji', '2026-10-10', None, 'festival', 'smetanovy-sady'),
    ev('flora-olomouc-hortikomplex-2026', 'Flora Olomouc – Hortikomplex 2026', '2026-10-08', '2026-10-11', 'vystava', 'pavilon-a', venueLabel='Celý areál', image=PH + 'ev-hortikomplex-2026.jpg',
       gallery=[PH + 'horti-1.jpg', PH + 'horti-2.jpg', PH + 'horti-3.jpg', PH + 'horti-4.jpg', PH + 'horti-5.jpg', PH + 'horti-6.jpg'],
       hours=hrs(('9:00', '17:00'), **{'2026_10_11': ('9:00', '16:00')}), prices=FLORA_PRICES,
       text='Podzimní mezinárodní zahradnická výstava s hlavní expozicí „Dary naší země“ v pavilonu A. Floristické show, kulinářské a pekařské show, soutěže Flora košt a Flora džem, vyřezávání dýní, festival gastronomie OLIMA, včelařská výstava Hanácká včela v pavilonu H, dýně v oranžerii, podzimní zahradnické trhy a hudba na pódiu SAMBA.'),
    ev('rozkvetle-pamatky-2026', 'Rozkvetlé památky 2026', '2026-10-08', '2026-10-18', 'vystava', 'oranzerie', venueLabel='Památky Olomouce'),
    ev('beh-a-pochod-pro-utulky', 'Běh a pochod pro útulky', '2026-09-27', None, 'sport', 'smetanovy-sady', external=True),
    ev('tattoo-expo-hana-2026', 'Tattoo Expo Haná 2026', '2026-09-19', '2026-09-20', 'festival', 'pavilon-a', external=True),
    ev('12-litr', 'LITR 2026 – knižní veletrh autorských publikací', '2026-09-18', '2026-09-20', 'veletrh', 'pavilon-a', external=True),
    ev('floracanis-2026', 'Floracanis 2026 – mezinárodní výstava psů', '2026-09-12', '2026-09-13', 'zvirata', 'pavilon-a', external=True),
    ev('vystava-myslivosti-a-prirody-olomouckeho-kraje-1', 'Výstava myslivosti a přírody Olomouckého kraje', '2026-09-10', '2026-09-19', 'vystava', 'pavilony-e-g-h', external=True),
    ev('babicka-roku-2026', 'Babička roku 2026', '2026-09-02', None, 'festival', 'pavilon-a', external=True),
    ev('happyplant', 'Happyplant – prodejní výstava pokojovek', '2026-08-29', None, 'trhy', 'pavilon-a', external=True),
    ev('santovka-family-day-2', 'Šantovka Family Day', '2026-08-29', None, 'festival', 'samba', external=True),
    ev('aquatera-2026', 'Aquatera – akvaristická a teraristická burza', '2026-08-22', None, 'trhy', 'pavilon-a', external=True),
    ev('festacek-2026', 'Festáček 2026', '2026-08-15', None, 'festival', 'samba', external=True),
    ev('bylinkobrani-1', 'Bylinkobraní', '2026-08-08', None, 'trhy', 'samba'),
    ev('letni-vinny-festival', 'Letní vinný festival', '2026-07-17', '2026-07-18', 'festival', 'samba', external=True),
    ev('den-s-novou-2026', 'Den s Novou 2026', '2026-06-27', None, 'festival', 'samba', external=True),
    ev('vystava-kaktusu-a-sukulentu-1', 'Výstava kaktusů a sukulentů', '2026-06-24', '2026-06-28', 'vystava', 'skleniky', text='Výstava s poradnou a prodejem rostlin ve sbírkových sklenících.'),
    ev('africke-trhy-v-olomouci', 'Africké trhy v Olomouci', '2026-06-20', None, 'trhy', 'samba', external=True),
    ev('moravia-sport-expo-2026', 'Moravia Sport Expo 2026', '2026-06-12', '2026-06-13', 'sport', 'pavilon-a', venueLabel='Celý areál',
       text='Největší sportovní hřiště v Olomouci: tisíce dětí, sportovní hvězdy a sporty, které možná objevíte poprvé.'),
    ev('vyznani-ruzim-2026', 'Vyznání růžím 2026 – Sběratelé růží', '2026-06-06', '2026-06-07', 'festival', 'rozarium', image=PH + 'ev-vyznani-ruzim-2026.jpg',
       gallery=[PH + 'ruze-1.jpg', PH + 'ruze-2.jpg', PH + 'ruze-3.jpg'], hours=hrs(('9:00', '19:00'), **{'2026_06_07': ('9:00', '18:00')}), prices=SKLENIK_EVENT_PRICES,
       text='Výstava a festival pod širým nebem pro milovníky růží, zahrad a dobrého jídla, letos s podtitulem Sběratelé růží. Slavnostní zahájení, křest růže „Josef Švejk“, floristické a kulinářské show, komentované prohlídky, přednášky o růžích v parfumerii, koncert JAMR’S, zóny Zahrada, Krása, Gastro, Art a Sport, prodej bylinek.'),
    ev('florinka-2026', 'Florinka 2026', '2026-06-06', '2026-06-07', 'deti', 'pavilony-e-g-h', venueLabel='Pavilon E'),
    ev('zive-pasti-2026', 'Živé pasti 2026 – masožravé rostliny', '2026-05-23', '2026-06-07', 'vystava', 'skleniky', image=PH + 'ev-zive-pasti-2026.jpg', gallery=[PH + 'pasti-1.jpg'],
       hours=hrs(('9:00', '18:00')), prices=SKLENIK_EVENT_PRICES,
       text='7. ročník prodejní výstavy masožravých rostlin ve sbírkových sklenících, letos s tématem pestře kvetoucích tučnic ze Střední Ameriky. Stovky rostlin rodů Drosera, Nepenthes, Dionaea, Sarracenia, Heliamphora, fotografie z expedice do Kambodže, poradna a prodej vzácných druhů, večerní prohlídky s autory.'),
    ev('swap-na-flore', 'SWAP na Floře', '2026-05-16', '2026-05-17', 'trhy', 'pavilony-e-g-h', external=True),
    ev('slavata-triatlon-tour-2026-vzeprit-se-osudu', 'Slavata triatlon tour 2026', '2026-05-13', None, 'sport', 'smetanovy-sady', external=True),
    ev('festival-jidla-sladkosti-a-zabavy', 'Festival jídla, sladkostí a zábavy', '2026-05-09', '2026-05-10', 'festival', 'samba', external=True),
    ev('flora-olomouc-2026', 'Flora Olomouc 2026 – Tóny Flory', '2026-04-23', '2026-04-26', 'vystava', 'pavilon-a', venueLabel='Celý areál', image=PH + 'ev-flora-olomouc-2026.jpg',
       gallery=[PH + 'flora-1.jpg', PH + 'flora-2.jpg', PH + 'flora-3.jpg', PH + 'flora-4.jpg', PH + 'flora-5.jpg'],
       hours=hrs(('9:00', '18:00'), **{'2026_04_26': ('9:00', '17:00')}), prices=FLORA_PRICES + [{'label': 'Večerní prohlídka', 'onsite': 290, 'online': 270}, {'label': 'Kombinované (den + večer)', 'onsite': 420, 'online': 400}],
       text='Největší svátek květin – mezinárodní květinová a zahradnická výstava. Hlavní expozice „Tóny Flory“ propojila květiny s hudbou. Pohár Flory (floristická soutěž), večerní prohlídka s jazzem, floristické show a přednášky v pavilonu A, workshopy v pavilonu C, bonsaje v pavilonu H, „Rozkvetlá partitura“ v oranžerii, zahradnické trhy s více než 300 prodejci, dětský program a rozhlasové pódium SAMBA.'),
    ev('for-model-2026', 'For Model 2026', '2026-03-27', '2026-03-29', 'vystava', 'pavilon-a', text='Výstava železničního modelářství: ukázka zahradní železnice a interaktivní kolejiště.'),
    ev('festival-zdravi', 'Festival zdraví', '2026-03-22', None, 'festival', 'pavilon-a', external=True),
    ev('svet-kamenu', 'Svět kamenů', '2026-03-22', None, 'trhy', 'pavilony-e-g-h', external=True),
    ev('ruze-ve-meste-mezinarodni-odborna-konference', 'Růže ve městě – mezinárodní odborná konference', '2026-03-20', None, 'konference', 'oranzerie'),
    ev('ples-mezi-kvety-2026', 'Ples mezi květy 2026', '2026-02-21', None, 'ples', 'pavilon-a'),
    ev('hobby-burza', 'Hobby burza', '2026-01-18', None, 'trhy', 'pavilon-a', external=True),
    ev('xxv-mestsky-bal', 'XXV. Městský bál', '2026-01-10', None, 'ples', 'pavilon-a', external=True),
]
for e in events:
    e.setdefault('external', False)

# tradiční akce bez potvrzeného termínu 2027 – jen orientačně
annual = [
    {'title': 'For Model', 'when': 'březen', 'what': 'železniční modelářství'},
    {'title': 'Flora Olomouc – jarní výstava', 'when': 'konec dubna', 'what': 'největší květinová výstava v ČR, zahradnické trhy'},
    {'title': 'Živé pasti', 'when': 'konec května – začátek června', 'what': 'masožravé rostliny ve sklenících'},
    {'title': 'Vyznání růžím', 'when': 'začátek června', 'what': 'festival v rozáriu v době kvetení růží'},
    {'title': 'Moravia Sport Expo', 'when': 'polovina června', 'what': 'sportovní festival pro děti i dospělé'},
    {'title': 'Výstava kaktusů a sukulentů', 'when': 'konec června', 'what': 'poradna a prodej ve sklenících'},
    {'title': 'Flora Olomouc – Hortikomplex', 'when': 'začátek října', 'what': 'podzimní zahradnická výstava, OLIMA, Hanácká včela'},
    {'title': 'Klenoty pralesa', 'when': 'druhá polovina října', 'what': 'orchideje a tropické rostliny v palmovém skleníku'},
    {'title': 'Svět kostek', 'when': 'přelom října a listopadu', 'what': 'mezinárodní výstava modelů ze stavebnic'},
    {'title': 'Stavotech', 'when': 'začátek listopadu', 'what': 'stavební veletrh Moderní dům'},
    {'title': 'Udržitelné Vánoce na Floře', 'when': 'konec listopadu', 'what': 'SWAP a trhy v pavilonu E'},
]

cats = [
    {'id': 'vystava', 'label': 'Výstavy'}, {'id': 'veletrh', 'label': 'Veletrhy'}, {'id': 'trhy', 'label': 'Trhy a burzy'}, {'id': 'koncert', 'label': 'Koncerty'},
    {'id': 'festival', 'label': 'Festivaly'}, {'id': 'sport', 'label': 'Sport'}, {'id': 'deti', 'label': 'Pro děti'}, {'id': 'zvirata', 'label': 'Zvířata'},
    {'id': 'ples', 'label': 'Plesy'}, {'id': 'konference', 'label': 'Konference'},
]

transport = {
    'tram': {'lines': ['1', '4', '6'], 'stop': 'Výstaviště Flora', 'note': 'Zastávka je přímo u pavilonu A. V době výstav jezdí posilové spoje.'},
    'bus': {'lines': ['16', '17', '28', '51'], 'stop': 'Smetanovy sady'},
    'train': 'Nejblíže je zastávka Olomouc město; k výstavišti dojdete i ze zastávky Olomouc-Nová Ulice.',
    'fromBusStation': 'Od autobusového nádraží tramvají č. 4.',
    'coach': 'Zájezdové autobusy vysazují návštěvníky u starého autobusového nádraží (tř. Svobody × Polská) a parkují na vyhrazené ploše naproti Baumaxu v Holické ulici.',
    'walk': 'Z Horního náměstí pěšky za pár minut.',
    'mhd': 'https://www.dpmo.cz/',
    'stops': [
        {'id': 'tram-vystaviste', 'name': 'Výstaviště Flora', 'kind': 'tram', 'lines': ['1', '4', '6'], 'gps': [49.58934, 17.24527]},
        {'id': 'tram-trznice', 'name': 'Tržnice', 'kind': 'tram', 'lines': ['1', '2', '3', '4', '6', '7'], 'gps': [49.58934, 17.25365]},
        {'id': 'tram-santovka', 'name': 'Šantovka', 'kind': 'tram', 'gps': [49.58778, 17.25796]},
        {'id': 'bus-smetanovy', 'name': 'Smetanovy sady', 'kind': 'bus', 'lines': ['16', '17', '28', '51'], 'gps': [49.58598, 17.25436]},
        {'id': 'train-smetanovy', 'name': 'Olomouc-Smetanovy sady (vlak)', 'kind': 'train', 'gps': [49.58556, 17.25486]},
    ],
}
MAP = json.load(open(ROOT / 'data' / 'map.json', encoding='utf-8')) if (ROOT / 'data' / 'map.json').exists() else None

parking = [
    {'id': 'santovka', 'name': 'Galerie Šantovka – parkoviště P6', 'cap': 'až 2 000 míst', 'dist': 'cca 10 minut pěšky', 'main': True,
     'note': 'Při akcích výstaviště zdarma – parkoviště je označeno „VYHRAZENO PRO VÝSTAVIŠTĚ FLORA OLOMOUC“. Mimo akce placené podle ceníku galerie; při hlavních výstavách Flora mohou platit jiná pravidla.',
     'url': 'https://www.galeriesantovka.cz/parkovani/', 'gps': [49.58707, 17.25763]},
    {'id': 'autobusove-nadrazi', 'name': 'Bývalé autobusové nádraží', 'dist': 'tř. Svobody × Polská, pár minut pěšky', 'note': 'Placené stání v centru.', 'gps': [49.58905, 17.2541]},
    {'id': 'pravnicka', 'name': 'U Právnické fakulty UP', 'dist': 'tř. 17. listopadu – blízko rozária', 'note': 'Vhodné pro návštěvu rozária a botanické zahrady.', 'gps': [49.59012, 17.26187]},
    {'id': 'hanackeho-pluku', 'name': 'Podzemní garáže Hanáckého pluku', 'dist': 'cca 10 minut pěšky', 'note': 'Placené garáže.', 'gps': [49.59667, 17.25737]},
    {'id': 'hlavni-nadrazi', 'name': 'Podzemní garáže u hlavního nádraží ČD', 'dist': 'dál, tramvají 1, 4 nebo 6 k výstavišti', 'note': 'Placené garáže.', 'gps': [49.5929, 17.278]},
    {'id': 'zamenhofova', 'name': 'Parkoviště v Zamenhofově ulici', 'dist': 'u areálu', 'note': 'Placené, omezená kapacita. Při hlavních výstavách vyhrazeno vystavovatelům a pro veřejnost uzavřeno.', 'gps': [49.58677, 17.24765]},
    {'id': 'areal', 'name': 'Parkoviště v areálu výstaviště', 'dist': '', 'note': 'Dvě placená parkoviště jsou při akcích vyhrazena vystavovatelům a personálu.', 'gps': [49.5885, 17.2445]},
]

tickets = {
    'online': 'https://akce.flora-ol.cz/vstupenky', 'phone': '+420 585 726 232', 'email': 'vstupenky@flora-ol.cz',
    'howto': ['Vstupenky na akce pořádané výstavištěm koupíte online na akce.flora-ol.cz nebo na pokladně při akci.', 'Online vstupenku netisknete – u vstupu stačí ukázat čárový kód v telefonu.',
              'Mnoho akcí pořádají externí organizátoři, kteří prodávají vstupenky sami (Ticketportal apod.) – ceny určují oni.'],
    'voucher': 'Dárkový poukaz na jednorázový vstup na jednu ze dvou hlavních výstav Flora Olomouc: online na akce.flora-ol.cz, e-mailem na vstupenky@flora-ol.cz (platba převodem), poštou nebo osobně v administrativní budově (Wolkerova 37/17, Alena Nádvorníková, platba kartou i hotově). Ke vstupu je vždy nutná platná vstupenka s čárovým kódem.',
    'vip': 'VIP karta: vstup zdarma pro 2 osoby na výstavy a veletrhy pořádané výstavištěm a do sbírkových skleníků. Nepřenosná, neplatí na akce externích pořadatelů. Aktivuje se registrací 13místného čísla pod čárovým kódem; u pokladny se karta načte před vstupem.',
    'vipUrl': 'https://akce.flora-ol.cz/darkove-poukazy-a-vip-karty',
}

news = [
    {'id': 'parkovani-svet-kostek', 'date': '2026-10-23', 'title': 'Kde zaparkovat na akci Svět kostek Olomouc 2026', 'url': 'https://www.flora-ol.cz/aktuality/kde-zaparkovat-na-akci-svet-kostek-olomouc-2026',
     'text': 'Parkování ve spolupráci s Galerií Šantovka: zdarma na parkovišti P6 označeném „VYHRAZENO PRO VÝSTAVIŠTĚ FLORA OLOMOUC“.'},
    {'id': 'hortikomplex-dary', 'date': '2026-09-16', 'title': 'Hortikomplex 2026 představí Dary naší země', 'url': 'https://www.flora-ol.cz/aktuality/flora-olomouc-hortikomplex-2026-predstavi-dary-nasi-zeme',
     'text': 'Podzimní výstava 8.–11. října s hlavní expozicí „Dary naší země“ v pavilonu A.'},
    {'id': 'rudolfova-alej-zahony', 'date': '2026-09-16', 'title': 'Květinové záhony v Rudolfově aleji projdou revitalizací', 'url': 'https://www.flora-ol.cz/aktuality/kvetinove-zahony-v-rudolfove-aleji-projdou-revitalizaci',
     'text': 'Ornamentální záhony v promenádě Smetanových sadů čeká obnova.'},
    {'id': 'trznice-kompetence', 'date': '2026-08-26', 'title': 'Olomoucká tržnice – kompetence', 'url': 'https://www.flora-ol.cz/aktuality/olomoucka-trznice-kompetence', 'text': 'Nová pravidla kompetencí pro městskou tržnici (ke stažení na webu).'},
    {'id': 'elektromobil', 'date': '2026-08-12', 'title': 'Výstaviště pořídilo nový elektromobil pro údržbu parků', 'url': 'https://www.flora-ol.cz/aktuality/vystaviste-flora-olomouc-poridilo-novy-elektromobil-pro-udrzbu-parku', 'text': 'Tichá a bezemisní údržba historických parků.'},
    {'id': 'narodni-sbirky', 'date': '2026-06-12', 'title': 'Flora Olomouc je nositelem dvou dalších Národních sbírek', 'url': 'https://www.flora-ol.cz/aktuality/vystaviste-flora-olomouc-je-nove-nositelem-dvou-dalsich-narodnich-sbirek', 'text': 'Po růžích a česneku (3. 6.) přibyly další dvě národní sbírky rostlin.'},
    {'id': 'mozart', 'date': '2026-06-09', 'title': 'Mozart u olomoucké radnice opět láká pozornost', 'url': 'https://www.flora-ol.cz/aktuality/mozart-u-olomoucke-radnice-opet-laka-pozornost-navstevniku', 'text': 'Květinová instalace zahradníků výstaviště v centru města.'},
]

data = {
    'meta': {'updated': UPDATED, 'source': 'https://www.flora-ol.cz/'},
    'center': center, 'places': places, 'events': events, 'annual': annual, 'cats': cats, 'transport': transport, 'parking': parking, 'tickets': tickets, 'news': news, 'map': MAP,
}
out = ROOT / 'data.js'
out.write_text('// Vygenerováno scripts/build-data.py z údajů webu flora-ol.cz – neupravovat ručně.\nwindow.FLORA_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print('data.js:', out.stat().st_size // 1024, 'KB;', len(places), 'míst,', len(events), 'akcí')
