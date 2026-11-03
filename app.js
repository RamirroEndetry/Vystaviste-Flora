/* Výstaviště Flora Olomouc – průvodce (prototyp). Vanilla JS, hash routing, data v data.js. */
(() => {
  'use strict';
  const D = window.FLORA_DATA;
  const $ = (sel, root = document) => root.querySelector(sel);
  const view = $('#view');
  const DAYS = ['Ne', 'Po', 'Út', 'St', 'Čt', 'Pá', 'So']; // Date.getDay()
  const DAYS_LONG = ['neděle', 'pondělí', 'úterý', 'středa', 'čtvrtek', 'pátek', 'sobota'];
  const DAYS_SHORT_ISO = ['Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne']; // 1..7
  const MONTHS = ['ledna', 'února', 'března', 'dubna', 'května', 'června', 'července', 'srpna', 'září', 'října', 'listopadu', 'prosince'];
  const MONTHS_NOM = ['Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen', 'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'];
  const STORE_KEY = 'vfo-app-v1';

  /* ---------- Úložiště ---------- */
  const state = Object.assign({ favs: [], parking: null, dismissed: [], theme: 'auto' }, load());
  function load() { try { return JSON.parse(localStorage.getItem(STORE_KEY) || '{}'); } catch { return {}; } }
  function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch { /* soukromý režim */ } }
  if (state.theme !== 'auto') document.documentElement.dataset.theme = state.theme;

  /* ---------- Čas (s možností simulace ?now=2026-11-06T10:40 pro testování) ---------- */
  let timeOffset = 0;
  (function initTime() {
    const m = location.search.match(/[?&]now=([^&]+)/);
    const sim = m ? decodeURIComponent(m[1]) : sessionStorage.getItem('vfo-now');
    if (sim) {
      const t = new Date(sim);
      if (!isNaN(t)) { timeOffset = t.getTime() - Date.now(); sessionStorage.setItem('vfo-now', sim); }
    }
  })();
  const now = () => new Date(Date.now() + timeOffset);
  const isSim = () => timeOffset !== 0;
  const isoDate = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const todayIso = () => isoDate(now());
  const fmtMin = (m) => `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`;
  const fmtClock = (d) => `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
  const fmtDate = (iso) => { const [y, mo, da] = iso.split('-').map(Number); return `${da}. ${mo}. ${y}`; };
  const fmtDateLong = (iso) => { const [, mo, da] = iso.split('-').map(Number); return `${da}. ${MONTHS[mo - 1]}`; };
  const fromIso = (iso) => { const [y, mo, da] = iso.split('-').map(Number); return new Date(y, mo - 1, da); };
  const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
  const isoDay = (d) => d.getDay() === 0 ? 7 : d.getDay(); // Po=1 … Ne=7
  const minutesOfDay = (d) => d.getHours() * 60 + d.getMinutes();
  const dateRange = (a, b) => { if (a === b) return fmtDate(a); const [ya, ma, da] = a.split('-').map(Number), [yb, mb, db] = b.split('-').map(Number); return ya === yb && ma === mb ? `${da}.–${db}. ${mb}. ${yb}` : `${da}. ${ma}. – ${db}. ${mb}. ${yb}`; };

  // Státní svátky ČR (parky mimo sezónu a infocentrum mají o svátcích zavřeno).
  const HOLIDAYS = new Set(['2026-01-01', '2026-04-03', '2026-04-06', '2026-05-01', '2026-05-08', '2026-07-05', '2026-07-06', '2026-09-28', '2026-10-28', '2026-11-17', '2026-12-24', '2026-12-25', '2026-12-26',
    '2027-01-01', '2027-03-26', '2027-03-29', '2027-05-01', '2027-05-08', '2027-07-05', '2027-07-06', '2027-09-28', '2027-10-28', '2027-11-17', '2027-12-24', '2027-12-25', '2027-12-26']);
  const isHoliday = (d) => HOLIDAYS.has(isoDate(d));

  /* ---------- Pomocné ---------- */
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const icon = (id, cls = '') => `<svg class="${cls}" aria-hidden="true"><use href="#i-${id}"/></svg>`;
  const placeById = Object.fromEntries(D.places.map((p) => [p.id, p]));
  const eventById = Object.fromEntries(D.events.map((e) => [e.id, e]));
  const catLabel = Object.fromEntries(D.cats.map((c) => [c.id, c.label]));
  const KIND = { pavilon: 'Pavilon', park: 'Park', zahrada: 'Zahrada', sklenik: 'Skleníky', gastro: 'Občerstvení', trznice: 'Tržnice' };
  const isFav = (id) => state.favs.includes(id);
  function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('is-on'); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('is-on'), 2600); }
  const tel = (p) => `tel:${String(p).replace(/\s/g, '')}`;
  const mapsUrl = (gps) => `https://maps.google.com/?q=${gps[0]},${gps[1]}`;
  const price = (n) => `${n.toLocaleString('cs')} Kč`;

  /* ---------- Otevírací doba míst (sezónní pravidla) ---------- */
  function spanFor(p, d) {
    const H = p.hours; if (!H) return null;
    if (H.always) return [0, 1440];
    const iso = isoDate(d), m = d.getMonth() + 1, wd = isoDay(d);
    if (H.overrides && H.overrides[iso]) return H.overrides[iso];
    const inRange = (r) => (!r.start || iso >= r.start) && (!r.end || iso <= r.end);
    if (H.holidaysOpen && H.holidaysOpen.includes(iso)) { const r = H.rules.find((x) => x.m.includes(m) && !x.closed && inRange(x)); if (r) return [r.o, r.c]; }
    const r = H.rules.find((x) => x.m.includes(m) && inRange(x));
    if (!r || r.closed || !r.d.includes(wd)) return null;
    if (r.hol === 'closed' && isHoliday(d)) return null;
    return [r.o, r.c];
  }
  /** Stav místa: {open, soon, cls, label, short} */
  function placeStatus(p, at = now()) {
    if (!p.hours) return { open: false, cls: 'na', label: 'Otevírací doba u provozovatele', short: '' };
    if (p.hours.always) return { open: true, cls: 'open', label: 'Volně přístupné, celoročně', short: 'otevřeno' };
    const today = spanFor(p, at), mins = minutesOfDay(at);
    if (today && mins >= today[0] && mins < today[1]) {
      const left = today[1] - mins;
      if (left <= 30) return { open: true, soon: true, cls: 'soon', label: `Zavírá za ${left} min`, short: `zavírá za ${left} min` };
      return { open: true, cls: 'open', label: `Otevřeno do ${fmtMin(today[1])}`, short: `do ${fmtMin(today[1])}` };
    }
    if (today && mins < today[0]) {
      const wait = today[0] - mins;
      return { open: false, cls: 'closed', label: wait <= 60 ? `Otevírá za ${wait} min` : `Dnes od ${fmtMin(today[0])}`, short: wait <= 60 ? `za ${wait} min` : `od ${fmtMin(today[0])}` };
    }
    for (let i = 1; i <= 120; i++) {
      const d = addDays(at, i), h = spanFor(p, d);
      if (h) {
        const when = i === 1 ? 'zítra' : i < 7 ? DAYS[d.getDay()] : fmtDateLong(isoDate(d));
        return { open: false, cls: 'closed', label: `Zavřeno · ${when} od ${fmtMin(h[0])}`, short: 'zavřeno' };
      }
    }
    return { open: false, cls: 'closed', label: 'Mimo sezónu zavřeno', short: 'zavřeno' };
  }
  const monthsLabel = (ms) => {
    const sorted = [...ms].sort((a, b) => a - b); const parts = [];
    for (let i = 0; i < sorted.length;) { let j = i; while (j + 1 < sorted.length && sorted[j + 1] === sorted[j] + 1) j++; parts.push(j > i ? `${MONTHS_NOM[sorted[i] - 1]}–${MONTHS_NOM[sorted[j] - 1].toLowerCase()}` : MONTHS_NOM[sorted[i] - 1]); i = j + 1; }
    return parts.join(', ');
  };
  const daysLabel = (ds) => (ds.length === 7 ? 'denně' : ds.length === 2 && ds.includes(6) && ds.includes(7) ? 'So–Ne' : ds.length === 5 && !ds.includes(6) ? 'Po–Pá' : ds.length === 6 && !ds.includes(1) ? 'Út–Ne' : ds.map((d) => DAYS_SHORT_ISO[d - 1]).join(', '));
  function hoursTable(p) {
    const H = p.hours; if (!H || H.always) return '';
    const m = now().getMonth() + 1;
    return `<table class="hours">${H.rules.map((r) => `<tr class="${r.m.includes(m) ? 'today' : ''}"><td>${esc(monthsLabel(r.m))}${r.start ? `<div class="tiny muted">od ${fmtDate(r.start)}${r.end ? ' do ' + fmtDate(r.end) : ''}</div>` : ''}</td><td>${r.closed ? 'zavřeno' : `${fmtMin(r.o)}–${fmtMin(r.c)}<div class="tiny muted">${esc(daysLabel(r.d))}${r.hol === 'closed' ? ', o svátcích zavřeno' : ''}</div>`}</td></tr>`).join('')}</table>`;
  }

  /* ---------- Akce ---------- */
  function eventState(e, t = todayIso()) { return e.end < t ? 'past' : e.start > t ? 'upcoming' : 'live'; }
  const eventHoursOn = (e, iso) => (e.hours ? e.hours[iso] || e.hours.default : null);
  /** Stav akce dnes / nejbližší den */
  function eventStatus(e, at = now()) {
    const st = eventState(e, isoDate(at));
    if (st === 'past') return { cls: 'na', label: 'Proběhlo', short: 'proběhlo' };
    if (st === 'upcoming') { const days = Math.round((fromIso(e.start) - fromIso(isoDate(at))) / 864e5); return { cls: 'na', label: days === 1 ? 'Zítra' : days < 7 ? `Za ${days} dny` : fmtDateLong(e.start), short: days === 1 ? 'zítra' : `za ${days} dní` }; }
    const h = eventHoursOn(e, isoDate(at)), mins = minutesOfDay(at);
    if (!h) return e.time ? { cls: 'open', label: `Dnes od ${e.time}${e.doors ? ` (vstup ${e.doors})` : ''}`, short: `od ${e.time}` } : { cls: 'open', label: 'Dnes', short: 'dnes' };
    if (mins < h[0]) return { cls: 'closed', label: `Dnes od ${fmtMin(h[0])}`, short: `od ${fmtMin(h[0])}` };
    if (mins >= h[1]) return { cls: 'closed', label: 'Dnes už skončilo', short: 'skončilo' };
    const left = h[1] - mins;
    return left <= 30 ? { open: true, cls: 'soon', label: `Končí za ${left} min`, short: `končí za ${left} min` } : { open: true, cls: 'open', label: `Otevřeno do ${fmtMin(h[1])}`, short: `do ${fmtMin(h[1])}` };
  }
  const venueName = (e) => e.venueLabel || (placeById[e.venue] ? placeById[e.venue].name : '');
  const sortedEvents = () => [...D.events].sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end));
  const liveEvents = () => sortedEvents().filter((e) => eventState(e) === 'live');
  const upcomingEvents = () => sortedEvents().filter((e) => eventState(e) === 'upcoming');

  function eventRow(e) {
    const st = eventState(e), [, m, d] = e.start.split('-'), es = eventStatus(e);
    return `<a class="item" href="#/akce/${e.id}">
      <div class="thumb thumb--date ${st === 'live' ? 'thumb--live' : ''}">${e.end === e.start ? `<b>${Number(d)}.</b><span>${MONTHS[Number(m) - 1].slice(0, 3)}</span>` : e.end.slice(0, 7) === e.start.slice(0, 7) ? `<b style="font-size:1rem">${Number(d)}.–${Number(e.end.slice(8))}.</b><span>${MONTHS[Number(m) - 1].slice(0, 3)}</span>` : `<b style="font-size:1rem">${Number(d)}.–${Number(e.end.slice(8))}.</b><span>${MONTHS[Number(m) - 1].slice(0, 3)}–${MONTHS[Number(e.end.slice(5, 7)) - 1].slice(0, 3)}</span>`}</div>
      <div class="item__body">
        <div class="item__name"><span>${esc(e.title)}</span>${isFav(e.id) ? `<span class="fav" aria-label="v mém programu">${icon('star')}</span>` : ''}</div>
        <div class="item__meta"><span>${esc(catLabel[e.cat] || '')}</span><span>· ${esc(venueName(e))}</span></div>
      </div>
      <div class="item__right">${st === 'live' ? '<span class="badge badge--brand">Probíhá</span>' : st === 'upcoming' ? '<span class="badge badge--gold">Chystá se</span>' : ''}<span class="status status--${es.cls} tiny">${esc(es.short)}</span></div>
    </a>`;
  }
  function eventCard(e) {
    return `<a class="evcard" href="#/akce/${e.id}">
      ${e.image ? `<img class="evcard__img" src="${esc(e.image)}" alt="" loading="lazy" decoding="async">` : `<div class="evcard__ph">${icon(e.cat === 'koncert' ? 'music' : 'flower')}</div>`}
      <div class="evcard__body"><div class="evcard__when">${esc(dateRange(e.start, e.end))}</div><div class="evcard__title">${esc(e.title)}</div><div class="evcard__venue">${esc(venueName(e))}</div></div></a>`;
  }
  function placeRow(p) {
    const st = placeStatus(p);
    return `<a class="item" href="#/misto/${p.id}">
      <div class="thumb">${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy" decoding="async">` : icon('tree')}</div>
      <div class="item__body"><div class="item__name"><span>${esc(p.name)}</span></div><div class="item__meta"><span>${esc(p.short)}</span></div></div>
      <div class="item__right">${p.free || (p.hours && p.hours.always) ? '<span class="badge badge--ok">zdarma</span>' : ''}<span class="status status--${st.cls} tiny">${esc(st.short)}</span></div>
    </a>`;
  }
  function pricesTable(prices) {
    if (!prices || !prices.length) return '';
    const hasOnline = prices.some((x) => x.online != null);
    return `<table class="hours">${hasOnline ? '<tr><td class="tiny muted">Kategorie</td><td class="tiny muted">na místě / online</td></tr>' : ''}${prices.map((x) => `<tr><td>${esc(x.label)}</td><td>${x.free ? 'zdarma' : hasOnline ? `${price(x.onsite)}${x.online != null ? ` / ${price(x.online)}` : ''}` : price(x.onsite)}</td></tr>`).join('')}</table>`;
  }
  const backBtn = () => `<button class="iconbtn iconbtn--ink" type="button" data-back aria-label="Zpět">${icon('back')}</button>`;

  /* ---------- Router ---------- */
  const routes = {
    dnes: renderHome, akce: renderEvents, parky: renderParks, areal: renderAreal, misto: renderPlace, vice: renderMore,
    vstupenky: renderTickets, doprava: renderTransport, parkovani: renderParking, kontakt: renderContact, program: renderProgram, aktuality: renderNews, kalendar: renderAnnual,
  };
  let currentQuery = {};
  function parseHash() {
    const raw = location.hash.replace(/^#\/?/, '') || 'dnes';
    const [path, qs = ''] = raw.split('?');
    const [route, ...rest] = path.split('/');
    const q = Object.fromEntries(new URLSearchParams(qs));
    return { route: routes[route] ? route : 'dnes', param: rest.join('/'), q };
  }
  function render() {
    const { route, param, q } = parseHash();
    currentQuery = q;
    view.innerHTML = routes[route](param, q) || '';
    const tab = { misto: 'parky', vstupenky: 'vice', doprava: 'vice', parkovani: 'vice', kontakt: 'vice', program: 'vice', aktuality: 'vice', kalendar: 'akce' }[route] || route;
    if (route === 'misto' && placeById[param] && ['pavilon', 'gastro', 'trznice'].includes(placeById[param].kind)) document.querySelectorAll('.tabbar a').forEach((a) => a.dataset.tab === 'areal' ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
    else document.querySelectorAll('.tabbar a').forEach((a) => (a.dataset.tab === tab ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
    if (!render.keepScroll) window.scrollTo(0, 0);
    render.keepScroll = false;
    renderTopStatus();
    afterRender(route, param);
  }
  function renderTopStatus() {
    const live = liveEvents().filter((e) => e.venue !== 'oranzerie');
    const d = now();
    let html = '';
    if (live.length) html = `Dnes: <b>${esc(live[0].title.replace(/ – .*$/, '').replace(/ \d{4}$/, ''))}</b>${live.length > 1 ? ` +${live.length - 1}` : ''}`;
    else { const st = placeStatus(placeById.skleniky); html = `Skleníky <b>${esc(st.short || st.label)}</b>`; }
    $('#topStatus').innerHTML = `${isSim() ? '<span class="pill-time" title="Simulovaný čas pro testování">TEST ' + fmtClock(d) + '</span> ' : ''}${html}`;
  }
  window.addEventListener('hashchange', render);

  /* ---------- Obrazovky ---------- */
  function greeting() { const h = now().getHours(); return h < 10 ? 'Dobré ráno' : h < 18 ? 'Dobrý den' : 'Dobrý večer'; }

  function renderHome() {
    const d = now(), t = todayIso();
    const live = liveEvents(), upcoming = upcomingEvents();
    const favs = state.favs.map((id) => eventById[id]).filter(Boolean).filter((e) => eventState(e) !== 'past');
    const quick = ['skleniky', 'rozarium', 'botanicka', 'food-park'].map((id) => placeById[id]);
    const next = upcoming[0];
    const headline = live.length ? (live.length === 1 ? 'Dnes se u nás koná' : `Dnes u nás: ${live.length} akce`) : next ? 'Nejbližší akce' : 'Vítejte na Floře';
    const sub = live.length ? live.map((e) => e.title).join(' · ') : next ? `${esc(next.title)} · ${dateRange(next.start, next.end)}` : 'Parky, skleníky a rozárium jsou tu pro vás po celý rok.';
    const news = [...D.news].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 2);
    return `
      <section class="card card--brand">
        <div class="row">
          <div class="grow">
            <div class="small" style="opacity:.85">${greeting()} · ${DAYS_LONG[d.getDay()]} ${d.getDate()}. ${MONTHS[d.getMonth()]}${isHoliday(d) ? ' · státní svátek' : ''}</div>
            <h1 style="margin-top:4px">${esc(headline)}</h1>
            <div class="small" style="margin-top:6px;opacity:.95">${sub}</div>
          </div>
          <a class="iconbtn" href="#/akce" aria-label="Všechny akce" style="background:rgba(255,255,255,.18)">${icon('cal')}</a>
        </div>
        <div class="statusbar">${quick.map((p) => { const st = placeStatus(p); return `<a href="#/misto/${p.id}"><span>${esc({ skleniky: 'Skleníky', rozarium: 'Rozárium', botanicka: 'Botanická zahrada', 'food-park': 'Food park' }[p.id] || p.name)}</span><b class="status status--${st.cls}">${esc(st.short || st.label)}</b></a>`; }).join('')}</div>
      </section>

      ${state.parking ? `<a class="card card--ok" href="#/parkovani" style="display:flex;gap:12px;align-items:center;margin-top:12px;text-decoration:none;color:inherit">${icon('car')}<div class="grow"><b>Auto stojí: ${esc(parkingName(state.parking.lot))}</b>${state.parking.spot ? ` · ${esc(state.parking.spot)}` : ''}</div>${icon('chev')}</a>` : ''}

      <section class="section">
        <div class="tiles">
          <a class="tile" href="#/akce">${icon('cal')}Akce</a>
          <a class="tile" href="#/vstupenky">${icon('ticket')}Vstupenky</a>
          <a class="tile" href="#/misto/skleniky">${icon('leaf')}Skleníky</a>
          <a class="tile" href="#/misto/rozarium">${icon('flower')}Rozárium</a>
          <a class="tile" href="#/areal">${icon('map')}Plán areálu</a>
          <a class="tile" href="#/doprava">${icon('tram')}Doprava</a>
        </div>
      </section>

      ${live.length ? `<section class="section"><div class="section__head"><h2>Právě probíhá</h2></div><div class="list">${live.map(eventRow).join('')}</div></section>` : ''}
      ${upcoming.length ? `<section class="section"><div class="section__head"><h2>Chystáme</h2><a href="#/akce">Všechny akce</a></div><div class="scroller">${upcoming.slice(0, 8).map(eventCard).join('')}</div></section>` : ''}

      ${favs.length ? `<section class="section"><div class="section__head"><h2>Můj program</h2><a href="#/program">Spravovat</a></div><div class="list">${favs.slice(0, 4).map(eventRow).join('')}</div></section>` : `<section class="section"><div class="card card--tint small"><b>Tip:</b> U akce klepněte na hvězdičku a budete ji mít tady na úvodu i se vstupným a hodinami.</div></section>`}

      <section class="section"><div class="section__head"><h2>Skleníky, zahrady a parky</h2><a href="#/parky">Vše</a></div><div class="list">${['skleniky', 'rozarium', 'botanicka', 'smetanovy-sady'].map((id) => placeRow(placeById[id])).join('')}</div></section>

      ${news.length ? `<section class="section"><div class="section__head"><h2>Aktuality</h2><a href="#/aktuality">Další</a></div><div class="stack">${news.map((n) => `<a class="card" href="${esc(n.url)}" target="_blank" rel="noopener" style="display:block;text-decoration:none;color:inherit"><div class="tiny muted">${fmtDate(n.date)}</div><b>${esc(n.title)}</b><div class="small muted" style="margin-top:4px">${esc(n.text)}</div></a>`).join('')}</div></section>` : ''}

      <p class="tiny muted" style="margin-top:24px">Neoficiální prototyp. Data z flora-ol.cz, stav k ${fmtDate(D.meta.updated)}. Otevírací doby a program se mohou změnit – rozhodující jsou informace pořadatele.</p>`;
  }

  /* ---------- Akce ---------- */
  function renderEvents(id, q) {
    if (id) { const e = eventById[id]; return e ? renderEventDetail(e) : `<div class="empty">Akce nenalezena. <a href="#/akce">Zpět na seznam</a></div>`; }
    const when = q.kdy || 'aktualni', cat = q.cat || '', text = q.q || '';
    const chips = [['aktualni', 'Aktuální'], ['probiha', 'Probíhá'], ['chysta', 'Chystá se'], ['archiv', 'Proběhlo']];
    return `
      <div class="page-head"><div class="grow"><h1>Akce a výstavy</h1><p class="sub">${D.events.length} akcí v roce 2026 · <a href="#/kalendar">tradiční kalendář</a></p></div></div>
      <div class="sticky">
        <div class="search">${icon('search')}<input id="q" type="text" inputmode="search" placeholder="Hledat akci, výstavu, koncert…" value="${esc(text)}" autocomplete="off" enterkeyhint="search" aria-label="Hledat akci"><button class="iconbtn iconbtn--ink ${text ? '' : 'hidden'}" id="qClear" type="button" aria-label="Smazat">${icon('x')}</button></div>
        <div class="chips" style="margin-top:8px">${chips.map(([k, l]) => `<button class="chip" type="button" data-set="kdy" data-val="${k}" aria-pressed="${when === k}">${l}</button>`).join('')}</div>
        <div class="chips"><button class="chip chip--small" type="button" data-set="cat" data-val="" aria-pressed="${!cat}">Vše</button>${D.cats.map((c) => `<button class="chip chip--small" type="button" data-set="cat" data-val="${c.id}" aria-pressed="${cat === c.id}">${esc(c.label)}</button>`).join('')}</div>
      </div>
      <div id="eventList" class="list" style="margin-top:8px"></div>`;
  }
  function filterEvents(q) {
    const t = norm(q.q || '').trim(), when = q.kdy || 'aktualni';
    let list = sortedEvents().filter((e) => {
      const st = eventState(e);
      if (when === 'aktualni' && st === 'past') return false;
      if (when === 'probiha' && st !== 'live') return false;
      if (when === 'chysta' && st !== 'upcoming') return false;
      if (when === 'archiv' && st !== 'past') return false;
      if (q.cat && e.cat !== q.cat) return false;
      return !t || norm(e.title).includes(t) || norm(venueName(e)).includes(t) || norm(catLabel[e.cat]).includes(t) || norm(e.text || '').includes(t);
    });
    if (when === 'archiv' || (t && when === 'aktualni' && !list.length)) list = (t ? sortedEvents().filter((e) => norm(e.title).includes(t) || norm(e.text || '').includes(t)) : list).reverse();
    return list;
  }
  function renderEventList() {
    const q = currentQuery, list = filterEvents(q), box = $('#eventList');
    if (!box) return;
    if (!list.length) { box.innerHTML = `<div class="empty">Nic jsme nenašli.<br><span class="small">Zkuste jiný výraz nebo jiné období.</span></div>`; return; }
    let html = `<div class="tiny muted" style="margin:4px 4px 0">${list.length} ${list.length === 1 ? 'akce' : list.length < 5 ? 'akce' : 'akcí'}</div>`;
    let last = '';
    for (const e of list) { const m = e.start.slice(0, 7); if (m !== last) { html += `<div class="letter">${MONTHS_NOM[Number(m.slice(5)) - 1].toUpperCase()} ${m.slice(0, 4)}</div>`; last = m; } html += eventRow(e); }
    box.innerHTML = html;
  }
  function setQuery(patch, replace = true) {
    const { route, param, q } = parseHash();
    const next = { ...q, ...patch };
    Object.keys(next).forEach((k) => (next[k] === '' || next[k] == null) && delete next[k]);
    const qs = new URLSearchParams(next).toString();
    render.keepScroll = true;
    const h = `#/${route}${param ? '/' + param : ''}${qs ? '?' + qs : ''}`;
    if (replace) history.replaceState(null, '', h); else location.hash = h;
    currentQuery = next;
  }
  function renderEventDetail(e) {
    const st = eventState(e), es = eventStatus(e), venue = placeById[e.venue];
    const hoursRows = e.hours ? Object.entries(e.hours).filter(([k]) => k !== 'default') : [];
    const days = []; if (e.hours) { for (let d = fromIso(e.start); isoDate(d) <= e.end && days.length < 31; d = addDays(d, 1)) days.push(isoDate(d)); }
    return `
      <div class="page-head">${backBtn()}<div class="grow"><p class="sub">${esc(catLabel[e.cat] || 'Akce')}${e.external ? ' · externí pořadatel' : ' · pořádá Výstaviště Flora'}</p></div><button class="iconbtn iconbtn--ink" type="button" data-fav="${e.id}" aria-pressed="${isFav(e.id)}" aria-label="${isFav(e.id) ? 'Odebrat z mého programu' : 'Přidat do mého programu'}"><svg viewBox="0 0 24 24" style="${isFav(e.id) ? 'fill:var(--gold);color:var(--gold)' : ''}"><use href="#i-star"/></svg></button></div>
      <section class="card">
        ${e.image ? `<img class="detail__img" src="${esc(e.image)}" alt="" style="margin-bottom:12px">` : ''}
        <h1 style="font-size:1.3rem">${esc(e.title)}</h1>
        <div class="row row--wrap" style="margin-top:8px"><span class="badge ${st === 'live' ? 'badge--brand' : st === 'upcoming' ? 'badge--gold' : ''}">${esc(dateRange(e.start, e.end))}</span>${e.time ? `<span class="badge">${esc(e.time)}${e.doors ? ` · vstup ${esc(e.doors)}` : ''}</span>` : ''}${e.hours ? `<span class="badge">${fmtMin(e.hours.default[0])}–${fmtMin(e.hours.default[1])}</span>` : ''}<span class="badge">${esc(venueName(e))}</span></div>
        <div style="margin-top:8px"><span class="status status--${es.cls}">${esc(es.label)}</span></div>
        <div class="actions">
          ${e.tickets || (!e.external && e.prices) ? `<a class="action" href="${esc(e.tickets || D.tickets.online)}" target="_blank" rel="noopener">${icon('ticket')}Vstupenky</a>` : `<span class="action" aria-disabled="true">${icon('ticket')}Na místě</span>`}
          ${venue ? `<a class="action" href="#/misto/${venue.id}">${icon('pin')}Kde to je</a>` : `<span class="action" aria-disabled="true">${icon('pin')}Místo</span>`}
          <a class="action" href="#/parkovani">${icon('car')}Parkování</a>
          <a class="action" href="${esc(e.web || e.url)}" target="_blank" rel="noopener">${icon('globe')}Web</a>
        </div>
      </section>
      ${e.text ? `<section class="card section"><h2>O akci</h2><p class="desc" style="margin-top:8px">${esc(e.text)}</p>${e.organizer ? `<p class="small muted" style="margin:6px 0 0">Pořadatel: ${esc(e.organizer)}</p>` : ''}</section>` : ''}
      ${days.length > 1 ? `<section class="card section"><h2>Otevřeno</h2><table class="hours" style="margin-top:8px">${days.map((iso) => { const h = eventHoursOn(e, iso); return `<tr class="${iso === todayIso() ? 'today' : ''}"><td>${DAYS[fromIso(iso).getDay()]} ${fmtDateLong(iso)}${iso === todayIso() ? ' <span class="tiny">(dnes)</span>' : ''}</td><td>${h ? `${fmtMin(h[0])}–${fmtMin(h[1])}` : '–'}</td></tr>`; }).join('')}</table></section>` : ''}
      ${e.prices ? `<section class="card section"><h2>Vstupné</h2><div style="margin-top:8px">${pricesTable(e.prices)}</div>${e.prices.some((x) => x.online != null) ? '<p class="tiny muted" style="margin:8px 0 0">Online vstupenky jsou levnější a netisknou se – u vstupu stačí čárový kód v telefonu.</p>' : ''}${e.external ? '<p class="tiny muted" style="margin:8px 0 0">Cenu vstupného určuje pořadatel akce.</p>' : ''}</section>` : e.external ? `<section class="card card--flat section small">Vstupné a prodej vstupenek zajišťuje pořadatel – Výstaviště Flora Olomouc akci pouze hostí.</section>` : ''}
      ${e.gallery ? `<section class="section"><div class="section__head"><h2>Fotografie</h2></div><div class="scroller gallery">${e.gallery.map((g) => `<img src="${esc(g)}" alt="" loading="lazy" decoding="async">`).join('')}</div></section>` : ''}
      ${venue ? `<section class="section"><div class="section__head"><h2>Místo konání</h2></div>${placeRow(venue)}</section>` : ''}
      <section class="card card--ok section notice">${icon('car')}<div class="small"><b>Parkování při akcích zdarma</b> na parkovišti P6 Galerie Šantovka (cca 10 minut pěšky). Tramvaje 1, 4 a 6 zastavují přímo u pavilonu A.</div></section>
      <section class="section stack"><a class="btn btn--ghost btn--block" href="${esc(e.url)}" target="_blank" rel="noopener">${icon('external')} Detail na akce.flora-ol.cz</a></section>`;
  }
  function renderAnnual() {
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Tradiční kalendář</h1><p class="sub">Akce, které se na Floře opakují každý rok</p></div></div>
      <div class="stack">${D.annual.map((a) => `<div class="card" style="display:flex;gap:12px;align-items:center"><div class="thumb thumb--date"><b style="font-size:.85rem">${esc(a.when.split(' ').slice(-1)[0].slice(0, 3))}</b></div><div class="grow"><b>${esc(a.title)}</b><div class="small muted">${esc(a.when)} · ${esc(a.what)}</div></div></div>`).join('')}</div>
      <p class="tiny muted" style="margin-top:14px">Termíny pro rok 2027 pořadatel zatím nezveřejnil – sledujte <a href="https://akce.flora-ol.cz" target="_blank" rel="noopener">akce.flora-ol.cz</a>.</p>`;
  }
  function renderProgram() {
    const favs = state.favs.map((id) => eventById[id]).filter(Boolean).sort((a, b) => a.start.localeCompare(b.start));
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Můj program</h1></div></div>
      <div class="list">${favs.length ? favs.map(eventRow).join('') : `<div class="empty">Zatím nemáte uložené akce.<br><a class="btn" style="margin-top:12px" href="#/akce">Procházet akce</a></div>`}</div>`;
  }

  /* ---------- Parky a areál ---------- */
  function renderParks() {
    const g1 = ['skleniky', 'rozarium', 'botanicka'].map((id) => placeById[id]);
    const g2 = D.places.filter((p) => p.kind === 'park');
    return `<div class="page-head"><div class="grow"><h1>Parky, skleníky a rozárium</h1><p class="sub">Historické parky cca 50 ha · vstup do parků, rozária a botanické zahrady zdarma</p></div></div>
      <section class="section" style="margin-top:0"><div class="section__head"><h2>Skleníky a zahrady</h2></div><div class="list">${g1.map(placeRow).join('')}</div></section>
      <section class="section"><div class="section__head"><h2>Historické parky</h2></div><div class="list">${g2.map(placeRow).join('')}</div></section>
      <section class="card card--flat section small">${icon('dog', 'ico')} Do rozária, botanické zahrady a skleníků je vstup se psem zakázán. Parky se uklízejí o víkendových ránech (cca 7–11 h). Závady hlaste na <a href="https://hlaseni.olomouc.eu/" target="_blank" rel="noopener">hlaseni.olomouc.eu</a>.</section>`;
  }
  function renderAreal() {
    const pav = D.places.filter((p) => p.kind === 'pavilon'), gastro = D.places.filter((p) => p.kind === 'gastro'), trz = placeById.trznice;
    return `<div class="page-head"><div class="grow"><h1>Plán areálu</h1><p class="sub">${esc(D.center.address)}</p></div></div>
      <section class="card card--hero"><img class="hero__img" src="assets/photos/areal-mapa.jpg" alt="Mapa: výstaviště leží u Smetanových sadů mezi Wolkerovou a Poupětovou ulicí"><div class="hero__body small">Areál leží na okraji <a href="#/misto/smetanovy-sady">Smetanových sadů</a>. Hlavní vstup a pokladny jsou u <a href="#/misto/pavilon-a">pavilonu A</a> (Wolkerova ulice, zastávka tramvaje Výstaviště Flora). Pavilony E, G, H a sbírkové skleníky jsou v parku, Food park mezi pavilony A a E. Při akcích vám poradí brigádníci u vstupů.<div class="row" style="margin-top:10px;gap:8px"><a class="btn btn--light grow" href="${mapsUrl(D.center.gps)}" target="_blank" rel="noopener">${icon('pin')} Navigovat</a><a class="btn btn--light grow" href="#/doprava">${icon('tram')} Doprava</a></div></div></section>
      <section class="section"><div class="section__head"><h2>Pavilony a plochy</h2></div><div class="list">${pav.map(placeRow).join('')}</div></section>
      <section class="section"><div class="section__head"><h2>Občerstvení</h2></div><div class="list">${gastro.map(placeRow).join('')}</div><p class="tiny muted" style="margin-top:8px">V rozáriu na tř. 17. listopadu funguje v otevírací době stánek Coffee Park.</p></section>
      <section class="section"><div class="section__head"><h2>Olomoucká tržnice</h2></div>${placeRow(trz)}</section>
      <section class="section"><div class="section__head"><h2>Sbírkové skleníky</h2></div>${placeRow(placeById.skleniky)}</section>`;
  }
  function renderPlace(id) {
    const p = placeById[id];
    if (!p) return `<div class="empty">Místo nenalezeno. <a href="#/parky">Zpět</a></div>`;
    const st = placeStatus(p), today = spanFor(p, now());
    const events = sortedEvents().filter((e) => e.venue === p.id && eventState(e) !== 'past').slice(0, 4);
    return `
      <div class="page-head">${backBtn()}<div class="grow"><p class="sub">${esc(KIND[p.kind] || '')}${p.address ? ` · ${esc(p.address)}` : ''}</p></div></div>
      <section class="card card--hero">
        ${p.image ? `<img class="hero__img" src="${esc(p.image)}" alt="">` : ''}
        <div class="hero__body detail__hero">
          <h1>${esc(p.name)}</h1>
          <div class="row row--wrap" style="margin-top:6px"><span class="status status--${st.cls}">${esc(st.label)}</span>${today && !(p.hours && p.hours.always) ? `<span class="tiny muted">dnes ${fmtMin(today[0])}–${fmtMin(today[1])}</span>` : ''}${p.free || (p.hours && p.hours.always) ? '<span class="badge badge--ok">vstup zdarma</span>' : ''}${p.dogs === false ? '<span class="badge badge--warn">bez psů</span>' : ''}</div>
          ${p.facts ? `<div class="facts">${p.facts.map((f) => `<span>${esc(f)}</span>`).join('')}</div>` : ''}
          <div class="actions">
            ${p.gps ? `<a class="action" href="${mapsUrl(p.gps)}" target="_blank" rel="noopener">${icon('pin')}Navigovat</a>` : ''}
            ${p.phone ? `<a class="action" href="${tel(p.phone)}">${icon('phone')}Zavolat</a>` : `<a class="action" href="#/kontakt">${icon('phone')}Kontakt</a>`}
            ${p.prices && !p.free ? `<a class="action" href="#/vstupenky">${icon('ticket')}Vstupenky</a>` : `<a class="action" href="#/parky">${icon('leaf')}Parky</a>`}
            <a class="action" href="${esc(p.url || D.center.web)}" target="_blank" rel="noopener">${icon('globe')}Web</a>
          </div>
        </div>
      </section>
      <section class="card section"><h2>O místě</h2><p class="desc" style="margin-top:8px">${esc(p.desc)}</p></section>
      ${p.sections ? `<section class="card section"><h2>Expozice</h2><div class="stack" style="margin-top:8px">${p.sections.map((s) => `<div><h3>${esc(s.name)}</h3><p class="small" style="margin:4px 0 0">${esc(s.text)}</p></div>`).join('')}</div></section>` : ''}
      ${p.vendors ? `<section class="card section"><h2>Provozovny</h2><div class="stack" style="margin-top:8px">${p.vendors.map((v) => `<div class="row"><div class="grow"><b>${esc(v.name)}</b><div class="small muted">${esc(v.what)}</div><div class="small">${esc(v.hours)}</div></div><a class="iconbtn iconbtn--ink" href="${esc(v.web)}" target="_blank" rel="noopener" aria-label="Web ${esc(v.name)}">${icon('external')}</a></div>`).join('')}</div></section>` : ''}
      ${p.hours && !p.hours.always ? `<section class="card section"><h2>Otevírací doba</h2><div style="margin-top:8px">${hoursTable(p)}</div>${p.hours.note ? `<p class="tiny muted" style="margin:8px 0 0">${esc(p.hours.note)}</p>` : ''}</section>` : p.hours && p.hours.note ? `<section class="card card--flat section small">${esc(p.hours.note)}</section>` : ''}
      ${p.prices ? `<section class="card section"><h2>${p.free ? 'Služby a ceny' : 'Vstupné'}</h2><div style="margin-top:8px">${pricesTable(p.prices)}</div></section>` : ''}
      ${events.length ? `<section class="section"><div class="section__head"><h2>Akce zde</h2></div><div class="list">${events.map(eventRow).join('')}</div></section>` : ''}
      ${p.gallery ? `<section class="section"><div class="section__head"><h2>Fotografie</h2></div><div class="scroller gallery">${p.gallery.map((g) => `<img src="${esc(g)}" alt="" loading="lazy" decoding="async">`).join('')}</div></section>` : ''}
      ${p.contact ? `<section class="card section"><h2>Kontakt</h2><p class="small" style="margin:8px 0 0">${esc(p.contact)}</p>${p.phone ? `<p class="small" style="margin:4px 0 0"><a href="${tel(p.phone)}">${esc(p.phone)}</a></p>` : ''}${p.phone2 ? `<p class="small" style="margin:4px 0 0">${esc(p.phone2)}</p>` : ''}${p.email ? `<p class="small" style="margin:4px 0 0"><a href="mailto:${esc(p.email)}">${esc(p.email)}</a></p>` : ''}</section>` : ''}`;
  }

  /* ---------- Více ---------- */
  function renderMore() {
    const items = [
      ['vstupenky', 'ticket', 'Vstupenky, poukazy a VIP karta'], ['doprava', 'tram', 'Jak se k nám dostat'], ['parkovani', 'car', 'Parkování'], ['areal', 'map', 'Plán areálu a pavilony'],
      ['misto/food-park', 'food', 'Food park a občerstvení'], ['misto/trznice', 'basket', 'Olomoucká tržnice'], ['kalendar', 'flower', 'Tradiční kalendář akcí'], ['aktuality', 'info', 'Aktuality'],
      ['kontakt', 'phone', 'Kontakt a otevírací doby'], ['program', 'star', `Můj program (${state.favs.length})`],
    ];
    return `<div class="page-head"><div class="grow"><h1>Více</h1></div></div>
      <div class="linklist">${items.map(([r, i, l]) => `<a href="#/${r}">${icon(i)}<span class="grow">${l}</span>${icon('chev', 'chev')}</a>`).join('')}</div>
      <section class="card section">
        <h2>Nastavení</h2>
        <div class="row" style="margin-top:10px;justify-content:space-between"><span class="small">Vzhled</span><div class="seg" role="group" aria-label="Vzhled">${['auto', 'light', 'dark'].map((t) => `<button type="button" data-theme="${t}" aria-pressed="${state.theme === t}">${{ auto: 'Auto', light: 'Světlý', dark: 'Tmavý' }[t]}</button>`).join('')}</div></div>
        <div class="row" style="margin-top:12px;justify-content:space-between;flex-wrap:wrap"><span class="small">Dotyková klávesnice</span><div class="seg" role="group" aria-label="Dotyková klávesnice">${['auto', 'on', 'off'].map((m) => `<button type="button" data-kbd-mode="${m}" aria-pressed="${(window.FloraKeyboard ? window.FloraKeyboard.mode() : 'auto') === m}">${{ auto: 'Auto', on: 'Zapnuta', off: 'Vypnuta' }[m]}</button>`).join('')}</div></div>
        <p class="tiny muted" style="margin:6px 0 0">Auto = na velkých dotykových panelech. Bez háčků a čárek – hledání je nerozlišuje.</p>
        <div class="row" style="margin-top:12px;justify-content:space-between"><span class="small">Spořič obrazovky (video pro infopanely)</span><button class="btn btn--sm btn--light" type="button" id="saverBtn">${icon('film')} Přehrát</button></div>
        <div id="installRow" class="row hidden" style="margin-top:12px;justify-content:space-between"><span class="small">Přidat aplikaci na plochu</span><button class="btn btn--sm" type="button" id="installBtn">Nainstalovat</button></div>
        ${isSim() ? `<div class="row" style="margin-top:12px;justify-content:space-between"><span class="small">Simulovaný čas: <b>${fmtClock(now())}, ${fmtDate(todayIso())}</b></span><button class="btn btn--sm btn--light" type="button" id="resetTime">Zrušit</button></div>` : ''}
      </section>
      <section class="card card--flat section small">
        <b>O aplikaci.</b> Neoficiální prototyp průvodce pro návštěvníky Výstaviště Flora Olomouc. Data (akce, otevírací doby, vstupné, parky) pocházejí z veřejných webů flora-ol.cz, akce.flora-ol.cz a parky.flora-ol.cz, stav k ${fmtDate(D.meta.updated)}. Váš program a poznámka o parkování zůstávají jen ve vašem zařízení.
        <div style="margin-top:8px"><a href="https://www.flora-ol.cz/" target="_blank" rel="noopener">flora-ol.cz</a> · <a href="https://akce.flora-ol.cz/navstevni-rad" target="_blank" rel="noopener">Návštěvní řád</a> · <a href="https://www.flora-ol.cz/nabidka-zamestnani" target="_blank" rel="noopener">Kariéra</a></div>
      </section>`;
  }
  function renderTickets() {
    const T = D.tickets;
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Vstupenky</h1></div></div>
      <section class="card card--brand"><div class="row">${icon('ticket')}<div class="grow"><b>Online je levněji.</b><div class="small" style="opacity:.9">Vstupenky na výstavy Flora Olomouc, Hortikomplex, Vyznání růžím, Svět kostek či do skleníků koupíte online se slevou. Netisknou se – stačí kód v telefonu.</div></div></div><a class="btn btn--light btn--block" style="margin-top:12px" href="${esc(T.online)}" target="_blank" rel="noopener">${icon('external')} Koupit online na akce.flora-ol.cz</a></section>
      <section class="card section"><h2>Jak to funguje</h2><ul class="small" style="margin:8px 0 0;padding-left:18px">${T.howto.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></section>
      <section class="card section"><h2>Sbírkové skleníky</h2><div style="margin-top:8px">${pricesTable(placeById.skleniky.prices)}</div><p class="tiny muted" style="margin:8px 0 0">${esc(placeById.skleniky.phone2)}. Výstavy ve sklenících (Živé pasti, Klenoty pralesa, kaktusy) mají vlastní vstupné.</p></section>
      <section class="card section"><h2>Dárkový poukaz</h2><p class="small" style="margin:8px 0 0">${esc(T.voucher)}</p></section>
      <section class="card section"><h2>VIP karta</h2><p class="small" style="margin:8px 0 0">${esc(T.vip)}</p><a class="btn btn--ghost btn--block" style="margin-top:10px" href="${esc(T.vipUrl)}" target="_blank" rel="noopener">${icon('external')} Poukazy a VIP karty</a></section>
      <section class="card card--flat section small">Hromadné objednávky, reklamace a dotazy: <a href="${tel(T.phone)}">${esc(T.phone)}</a>, <a href="mailto:${esc(T.email)}">${esc(T.email)}</a> (${esc(D.center.tickets.person)}).</section>`;
  }
  function renderTransport() {
    const T = D.transport;
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Jak se k nám dostat</h1></div></div>
      <section class="card">
        <h2>${icon('tram', 'ico')} Tramvají</h2>
        <p class="small" style="margin-top:8px">Zastávka <b>${esc(T.tram.stop)}</b> – ${esc(T.tram.note)}</p>
        <div class="lines">${T.tram.lines.map((l) => `<span class="line">${l}</span>`).join('')}</div>
      </section>
      <section class="card section">
        <h2>Autobusem MHD</h2>
        <p class="small" style="margin-top:8px">Zastávka <b>${esc(T.bus.stop)}</b>.</p>
        <div class="lines">${T.bus.lines.map((l) => `<span class="line line--bus">${l}</span>`).join('')}</div>
        <p class="tiny muted" style="margin:10px 0 0">${esc(T.fromBusStation)} Jízdní řády: <a href="${esc(T.mhd)}" target="_blank" rel="noopener">dpmo.cz</a>.</p>
      </section>
      <section class="card section"><h2>Vlakem a pěšky</h2><p class="small" style="margin-top:8px">${esc(T.train)} ${esc(T.walk)}</p></section>
      <section class="card section"><h2>Zájezdovým autobusem</h2><p class="small" style="margin-top:8px">${esc(T.coach)}</p></section>
      <section class="card section">
        <h2>${icon('car', 'ico')} Autem</h2>
        <p class="small" style="margin-top:8px">Výstaviště leží na hlavním příjezdu od Brna; od Ostravy a Mohelnice se napojíte přes vnější obchvat, dostupné je i z vnitřního městského okruhu. Při akcích parkujte zdarma na P6 u Galerie Šantovka. <a href="#/parkovani">Všechna parkoviště</a>.</p>
        <a class="btn btn--light btn--block" href="${mapsUrl(D.center.gps)}" target="_blank" rel="noopener">${icon('pin')} Navigovat k pavilonu A</a>
      </section>`;
  }
  const parkingName = (id) => (D.parking.find((p) => p.id === id) || {}).name || id;
  function renderParking() {
    const p = state.parking;
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Parkování</h1><p class="sub">Parkoviště v areálu jsou při akcích vyhrazena vystavovatelům</p></div></div>
      ${p ? `<section class="card card--brand"><div class="row"><div class="grow"><div class="small" style="opacity:.9">Zaparkováno ${fmtClock(new Date(p.at))}</div><div class="big" style="font-size:1.4rem;margin-top:6px">${esc(parkingName(p.lot))}</div>${p.spot ? `<div class="small" style="margin-top:4px">${esc(p.spot)}</div>` : ''}</div></div><div class="row" style="margin-top:14px;gap:8px">${(D.parking.find((x) => x.id === p.lot) || {}).gps ? `<a class="btn btn--light grow" href="${mapsUrl(D.parking.find((x) => x.id === p.lot).gps)}" target="_blank" rel="noopener">${icon('pin')} K autu</a>` : ''}<button class="btn btn--danger" type="button" data-endpark>Odjíždím</button></div></section>`
        : `<section class="card"><h2>Kde jsem zaparkoval(a)</h2><p class="small muted" style="margin-top:4px">Poznamenejte si parkoviště a místo – po výstavě se vám bude hodit.</p>
        <form id="parkForm" class="stack" style="margin-top:10px">
          <label class="field">Parkoviště<select name="lot">${D.parking.map((x) => `<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select></label>
          <label class="field">Kde stojím (volitelné)<input type="text" name="spot" placeholder="např. řada C, u vjezdu, modrý sloup" maxlength="60"></label>
          <button class="btn btn--block" type="submit">${icon('car')} Zapamatovat</button>
        </form></section>`}
      <section class="section"><div class="section__head"><h2>Kde zaparkovat</h2></div><div class="stack">${D.parking.map((x) => `<div class="card ${x.main ? 'card--ok' : 'card--flat'}"><div class="row"><div class="grow"><b>${esc(x.name)}</b>${x.cap ? ` <span class="badge">${esc(x.cap)}</span>` : ''}<div class="small muted">${esc(x.dist)}</div><div class="small" style="margin-top:4px">${esc(x.note)}</div></div>${x.gps ? `<a class="iconbtn iconbtn--ink" href="${mapsUrl(x.gps)}" target="_blank" rel="noopener" aria-label="Navigovat">${icon('pin')}</a>` : ''}</div>${x.url ? `<a class="small" href="${esc(x.url)}" target="_blank" rel="noopener">Aktuální podmínky a ceník</a>` : ''}</div>`).join('')}</div></section>
      <section class="card card--flat section small">Zájezdové autobusy: vystoupení u starého autobusového nádraží (tř. Svobody × Polská), parkování na vyhrazené ploše naproti Baumaxu v Holické ulici. Podrobnosti k parkování na konkrétní akci bývají na stránce akce.</section>`;
  }
  function renderContact() {
    const C = D.center;
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Kontakt a otevírací doby</h1></div></div>
      <section class="card">
        <table class="hours">${['skleniky', 'rozarium', 'botanicka', 'food-park', 'trznice'].map((id) => { const p = placeById[id], st = placeStatus(p), h = spanFor(p, now()); return `<tr><td><a href="#/misto/${p.id}" style="font-weight:700;text-decoration:none">${esc(p.name)}</a><div class="tiny"><span class="status status--${st.cls}">${esc(st.label)}</span></div></td><td>${h ? `${fmtMin(h[0])}–${fmtMin(h[1])}` : 'dnes zavřeno'}<div class="tiny muted">dnes (${DAYS_LONG[now().getDay()]})</div></td></tr>`; }).join('')}</table>
        <p class="tiny muted" style="margin:10px 0 0">Historické parky jsou přístupné celoročně. Pavilony jsou otevřené podle programu konkrétní akce.</p>
      </section>
      <section class="card section">
        <h2>${esc(C.company)}</h2>
        <dl class="kv" style="margin-top:10px"><dt>Adresa</dt><dd style="text-align:right">${esc(C.address)}</dd><dt>Ústředna</dt><dd><a href="${tel(C.phone)}">${esc(C.phone)}</a></dd><dt>E-mail</dt><dd><a href="mailto:${esc(C.email)}">${esc(C.email)}</a></dd><dt>Vstupenky</dt><dd><a href="${tel(C.tickets.phone)}">${esc(C.tickets.phone)}</a></dd><dt>IČO</dt><dd>${esc(C.ico)}</dd><dt>Datová schránka</dt><dd>${esc(C.datovka)}</dd></dl>
        <div class="row" style="margin-top:12px;gap:8px"><a class="btn btn--light grow" href="${mapsUrl(C.gps)}" target="_blank" rel="noopener">${icon('pin')} Navigovat</a><a class="btn btn--light grow" href="${tel(C.phone)}">${icon('phone')} Zavolat</a></div>
        <p class="tiny muted" style="margin:10px 0 0">Společnost je ve 100% vlastnictví statutárního města Olomouce. Sídlo je v administrativní budově u pavilonu A.</p>
      </section>
      <section class="card section"><h2>Sledujte nás</h2><div class="row row--wrap" style="margin-top:8px;gap:8px"><a class="btn btn--light btn--sm" href="${esc(C.social.facebook)}" target="_blank" rel="noopener">Facebook</a><a class="btn btn--light btn--sm" href="${esc(C.social.instagram)}" target="_blank" rel="noopener">Instagram</a><a class="btn btn--light btn--sm" href="${esc(C.social.youtube)}" target="_blank" rel="noopener">YouTube</a></div></section>
      <section class="card card--tint section small"><b>Zajímavosti:</b> ${C.facts.join(' · ')}.</section>`;
  }
  function renderNews() {
    const items = [...D.news].sort((a, b) => b.date.localeCompare(a.date));
    return `<div class="page-head">${backBtn()}<div class="grow"><h1>Aktuality</h1></div></div>
      <div class="stack">${items.map((n) => `<a class="card" href="${esc(n.url)}" target="_blank" rel="noopener" style="display:block;text-decoration:none;color:inherit"><div class="tiny muted">${fmtDate(n.date)}</div><b>${esc(n.title)}</b><div class="small muted" style="margin-top:4px">${esc(n.text)}</div></a>`).join('')}</div>
      <p class="tiny muted" style="margin-top:14px">Všechny aktuality: <a href="https://www.flora-ol.cz/aktuality" target="_blank" rel="noopener">flora-ol.cz/aktuality</a>.</p>`;
  }

  /* ---------- Chování po vykreslení ---------- */
  function afterRender(route) {
    if (route === 'akce' && $('#eventList')) {
      renderEventList();
      const q = $('#q');
      q.addEventListener('input', () => { setQuery({ q: q.value }); $('#qClear').classList.toggle('hidden', !q.value); renderEventList(); });
      $('#qClear').addEventListener('click', () => { q.value = ''; setQuery({ q: '' }); $('#qClear').classList.add('hidden'); renderEventList(); q.focus(); });
      if (currentQuery.focus) q.focus();
    }
    if (route === 'vice') {
      if (deferredInstall) $('#installRow').classList.remove('hidden');
      $('#saverBtn')?.addEventListener('click', () => window.FloraSaver && window.FloraSaver.show(true));
      $('#installBtn')?.addEventListener('click', async () => { deferredInstall.prompt(); await deferredInstall.userChoice; deferredInstall = null; $('#installRow').classList.add('hidden'); });
      $('#resetTime')?.addEventListener('click', () => { sessionStorage.removeItem('vfo-now'); location.href = location.pathname + '#/vice'; location.reload(); });
    }
    renderTopStatus();
  }

  /* ---------- Události (delegace) ---------- */
  view.addEventListener('click', (e) => {
    const t = e.target.closest('[data-back],[data-set],[data-fav],[data-endpark],[data-theme],[data-kbd-mode]');
    if (!t) return;
    if (t.dataset.kbdMode) { window.FloraKeyboard && window.FloraKeyboard.setMode(t.dataset.kbdMode); render.keepScroll = true; render(); return; }
    if (t.hasAttribute('data-back')) { e.preventDefault(); history.length > 1 ? history.back() : (location.hash = '#/dnes'); return; }
    if (t.dataset.set !== undefined) { setQuery({ [t.dataset.set]: t.dataset.val }); render.keepScroll = true; render(); return; }
    if (t.dataset.fav) {
      const id = t.dataset.fav, i = state.favs.indexOf(id);
      i >= 0 ? state.favs.splice(i, 1) : state.favs.push(id); save();
      toast(i >= 0 ? 'Odebráno z mého programu' : 'Přidáno do mého programu'); render.keepScroll = true; render(); return;
    }
    if (t.hasAttribute('data-endpark')) { state.parking = null; save(); render(); toast('Šťastnou cestu!'); return; }
    if (t.dataset.theme) { state.theme = t.dataset.theme; save(); if (state.theme === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = state.theme; render.keepScroll = true; render(); return; }
  });
  view.addEventListener('submit', (e) => {
    if (e.target.id === 'parkForm') {
      e.preventDefault();
      const f = new FormData(e.target);
      state.parking = { lot: String(f.get('lot')), spot: String(f.get('spot') || '').trim(), at: now().toISOString() };
      save(); render(); toast('Zapamatováno');
    }
  });
  $('#btnSearch').addEventListener('click', () => { location.hash = '#/akce?focus=1'; });

  /* ---------- PWA ---------- */
  let deferredInstall = null;
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredInstall = e; $('#installRow')?.classList.remove('hidden'); });
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(() => {});

  render();
  setInterval(renderTopStatus, 60000);
})();
