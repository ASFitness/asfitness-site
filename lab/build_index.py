#!/usr/bin/env python3
"""Pune secțiunile din lab/nou.html pe pagina principală (index.html).

- CSS-ul din lab primește prefixul `.nx ` ca să nu se bată cu stilurile site-ului.
- Vechiul „hero” e înlocuit cu: încărcare + cronometru (logo spart) + scanare + Drumul tău + Arsenalul tău.
- „Din iulie 2025” + „ME vs me” intră înainte de Abonamente.
- Textele primesc data-t (traducere EN prin dicționarul existent).
Rulare: python3 lab/build_index.py (din folderul asfitness-site). Idempotent: lucrează pe index.html curent
doar dacă nu conține deja blocul nou.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
lab = (ROOT / 'lab' / 'nou.html').read_text()
scan_css = (ROOT / 'lab' / 'scan.css').read_text()
index = (ROOT / 'index.html').read_text()
if 'id="launch"' in index:
    sys.exit('index.html are deja secțiunile noi')

# ---------- CSS ----------
def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)

SKIP = re.compile(r'^(:root|\*|html(?!\[)|body|header|a|\.wm|\.pill|\.rest|\.foot|\.mono)\b')

def block_end(css, i):
    depth = 0
    for j in range(i, len(css)):
        if css[j] == '{': depth += 1
        elif css[j] == '}':
            depth -= 1
            if depth == 0: return j
    raise ValueError('acoladă neînchisă')

def prefix_css(css):
    out, i = [], 0
    while True:
        j = css.find('{', i)
        if j < 0: break
        sel = css[i:j].strip()
        end = block_end(css, j)
        body = css[j + 1:end]
        if sel.startswith('@media') or sel.startswith('@supports'):
            inner = prefix_css(body)
            if inner.strip(): out.append(f'{sel} {{\n{inner}\n}}')
        elif sel.startswith('@keyframes'):
            out.append(f'{sel} {{{body}}}')
        else:
            parts = [p.strip() for p in sel.split(',')]
            keep = [p for p in parts if not SKIP.match(p)]
            if keep:
                out.append(', '.join((p.replace('html[lang=en] ', 'html[lang=en] .nx ', 1) if p.startswith('html[') else '.nx ' + p) for p in keep) + ' {' + body + '}')
        i = end + 1
    return '\n'.join(out)

lab_css = strip_comments(lab[lab.index('<style>') + 7: lab.index('</style>')])
css = prefix_css(strip_comments(scan_css)) + '\n' + prefix_css(lab_css)
css = css.replace('../img/', 'img/')
css += '''
  /* potriviri cu stilurile site-ului */
  .nx section { padding: 0; }
  .nx .kicker::before { display: none; }
  .nx h2 { letter-spacing: normal; text-wrap: balance; }
  .nx img { max-width: none; }
  .nx .hbot .alt { display: flex; gap: 18px; justify-content: center; font: 500 13px/1 'DM Sans'; }
  .nx .hbot .alt a, .nx .hbot .alt button { all: unset; cursor: pointer; color: rgba(237,233,254,.75); text-decoration: underline; text-underline-offset: 3px; }
  body.lock { overflow: hidden; }
'''

# ---------- HTML ----------
def cut(a, b):
    return lab[lab.index(a): lab.index(b)]

loader = cut('<!-- 1. ÎNCĂRCARE -->', '<header>')
top = cut('<!-- 2. NUMĂRĂTOAREA -->', '<!-- DIN 2025 (povestea) -->')
bottom = cut('<!-- DIN 2025 (povestea) -->', '<div class="rest">')

def fix(html):
    html = html.replace('../img/', 'img/').replace("'../app/'", "'app/'")
    return html

top, bottom, loader = fix(top), fix(bottom), fix(loader)

# legături: „Fă primul pas” deschide quiz-ul de pe site
top = top.replace('<a class="go-btn dcta" id="dcta" href="../#primul-pas">Fă primul pas</a>',
                  '<button type="button" class="go-btn dcta" id="dcta" data-quiz data-t="nx_step">Fă primul pas</button>')
bottom = bottom.replace('<a class="go-btn msub" id="mgo" href="../#primul-pas">Fă primul pas</a>',
                        '<button type="button" class="go-btn msub" id="mgo" data-quiz data-t="nx_step">Fă primul pas</button>')
bottom = bottom.replace('<div class="pl"><a href="#launch">Povestea ASFitness</a><a class="arr" href="#launch">→</a></div>',
                        '<div class="pl"><a href="#povestea" data-t="nx_pov_btn">O zi cu ASFitness</a><a class="arr" href="#povestea">→</a></div>')

# sub butonul „Anunță-mă”: quiz + cont
top = top.replace('<button class="cta" data-notify><img src="img/icon-512.png" alt="" />Anunță-mă la lansare</button>',
                  '<button class="cta" data-notify data-umami-event="notify_launch_open"><img src="img/icon-512.png" alt="" /><span data-t="nx_notify">Anunță-mă la lansare</span></button>\n'
                  '      <div class="alt"><button type="button" data-quiz data-t="nx_quiz">Fă primul pas · 1 minut</button><a href="https://asfitness-app.expo.app" target="_blank" rel="noopener" data-umami-event="have_account" data-t="cta_have">Am deja cont</a></div>')

T = {  # textul român exact din pagină -> (cheie, engleză)
    '<div class="kick">LANSARE · 01.01.2027 · 00:00</div>': ('nx_kick', 'LAUNCH · 01.01.2027 · 00:00'),
    '<span class="u">ZILE</span>': ('nx_d', 'DAYS'), '<span class="u">ORE</span>': ('nx_h', 'HOURS'),
    '<span class="u">MINUTE</span>': ('nx_m', 'MINUTES'), '<span class="u">SECUNDE</span>': ('nx_s', 'SECONDS'),
    '<div class="bigdone">AM LANSAT</div>': ('nx_done', 'WE ARE LIVE'),
    '<p>Pe <b>1 ianuarie 2027</b> lansăm ASFitness: antrenament, nutriție, refacere și echipă, într-o singură aplicație.</p>':
        ('nx_l1', 'On <b>1 January 2027</b> we launch ASFitness: training, nutrition, recovery and team, in one app.'),
    '<p class="m" style="display:none">Lansăm pe <b>1 ianuarie 2027</b>.</p>': ('nx_lm', 'We launch on <b>1 January 2027</b>.'),
    '<p class="r">De ce 1 ianuarie? E ziua în care toată lumea promite că se schimbă. <b>Noi îți dăm cu ce.</b></p>':
        ('nx_l2', 'Why 1 January? It is the day everyone promises to change. <b>We give you the tools.</b>'),
    '<h3>Fii primul.</h3>': ('nx_dh', 'Be the first.'),
    '<p>Îți trimitem un singur email, pe 1 ianuarie 2027, când aplicația e live. Fără spam.</p>':
        ('nx_dp', 'We send you one email, on 1 January 2027, when the app goes live. No spam.'),
    '<small>Prototip: deocamdată adresa nu se salvează.</small>': ('nx_dsm', 'Only for the launch email. You can ask us to delete it at contact@asfitness.ro.'),
    '<div class="kicker">Scanare ASF</div>': ('nx_sk', 'ASF scan'),
    '<h2>Aplicația te vede <em>întreg</em>.</h2>': ('nx_sh', 'The app sees <em>all of you</em>.'),
    '<p>Somn, mușchi, încărcare, nutriție și ciclul menstrual: totul se adaptează corpului tău, fie că ești băiat sau fată.</p>':
        ('nx_sp', 'Sleep, muscles, load, nutrition and the menstrual cycle: everything adapts to your body, whether you are a man or a woman.'),
    '<button id="bm" class="on" role="tab">BĂIAT</button>': ('nx_bm', 'MAN'),
    '<button id="bf" role="tab">FATĂ</button>': ('nx_bf', 'WOMAN'),
    '<div class="note">Cifrele sunt un exemplu. În aplicație vezi datele tale reale.</div>': ('nx_note', 'The numbers are an example. In the app you see your real data.'),
    '<div class="kicker">Drumul tău</div>': ('nx_dk', 'Your journey'),
    '<h2>De la primul pas <small>până la</small><br />cel mai bun tu</h2>': ('nx_dh2', 'From the first step <small>to</small><br />the best you'),
    '<strong>Chestionarul</strong><span>2 minute: sport, obiectiv, program.</span>': ('nx_d1', '<strong>The questionnaire</strong><span>2 minutes: sport, goal, schedule.</span>'),
    '<strong>Planul tău</strong><span>Antrenament și mese făcute pentru tine.</span>': ('nx_d2', '<strong>Your plan</strong><span>Training and meals made for you.</span>'),
    '<strong>Antrenament</strong><span>Fiecare serie și repetare, salvate.</span>': ('nx_d3', '<strong>Training</strong><span>Every set and rep, saved.</span>'),
    '<strong>Refacere</strong><span>Somn, WHOOP, dureri: știi când să tragi și când să te oprești.</span>': ('nx_d4', '<strong>Recovery</strong><span>Sleep, WHOOP, pain: know when to push and when to stop.</span>'),
    '<strong>Progres</strong><span>Recorduri, insigne, ME vs me.</span>': ('nx_d5', '<strong>Progress</strong><span>Records, badges, ME vs me.</span>'),
    '<div class="ghost" id="ghost">Arsenalul tău · Arsenalul tău</div>': ('nx_ghost', 'Your arsenal · Your arsenal'),
    '<h4>Azi</h4><div class="st">Check-in · WHOOP · ce faci azi</div>': ('nx_c1', '<h4>Today</h4><div class="st">Check-in · WHOOP · what to do today</div>'),
    '<h4>Antrenament</h4><div class="st">Program generat · RIR · recorduri</div>': ('nx_c2', '<h4>Training</h4><div class="st">Generated program · RIR · records</div>'),
    '<h4>Nutriție</h4><div class="st">Calorii · macro · cod de bare</div>': ('nx_c3', '<h4>Nutrition</h4><div class="st">Calories · macros · barcode</div>'),
    '<h4>Chef ASF</h4><div class="st">Rețete · meal prep · listă</div>': ('nx_c4', '<h4>Chef ASF</h4><div class="st">Recipes · meal prep · list</div>'),
    '<h4>Misiuni</h4><div class="st">XP · insigne · Rookie → Legend</div>': ('nx_c5', '<h4>Missions</h4><div class="st">XP · badges · Rookie → Legend</div>'),
    '<h4>Echipa</h4><div class="st">Antrenor · chat · clasament</div>': ('nx_c6', '<h4>Team</h4><div class="st">Coach · chat · leaderboard</div>'),
    '<div class="arsenal-hint">DERULEAZĂ ↓</div>': ('nx_hint', 'SCROLL ↓'),
    '<h2>Din <small>iulie</small> 2025,<br />construim sportivi<br /><small>mai buni</small> decât ieri</h2>':
        ('nx_ph', 'Since <small>July</small> 2025,<br />building athletes<br /><small>better</small> than yesterday'),
    '<p>ASFitness a pornit în iulie 2025, de la un antrenor care își urmărea sportivii în Excel. Azi e o aplicație completă, construită zi de zi, pentru sportivii din România și de peste tot.</p>':
        ('nx_pp', 'ASFitness started in July 2025, with a coach tracking his athletes in Excel. Today it is a complete app, built day by day, for athletes in Romania and everywhere.'),
    '<p class="msub" id="msub">Nu te compari cu nimeni. Te compari cu tine de ieri. Fiecare antrenament, fiecare masă și fiecare noapte de somn te fac puțin mai bun.</p>':
        ('nx_ms', 'You do not compare yourself to anyone. You compare yourself to yesterday’s you. Every workout, every meal and every night of sleep makes you a little better.'),
}
EN_ENTRIES = {'nx_step': 'Take the first step', 'nx_pov_btn': 'A day with ASFitness', 'nx_notify': 'Notify me at launch', 'nx_quiz': 'Take the first step · 1 minute'}

def add_t(html):
    for ro, (key, en) in T.items():
        if ro not in html: continue
        m = re.match(r'<(\w+)([^>]*)>(.*)</\1>$', ro, re.S)
        if m and ro.count('<' + m.group(1)) == 1:  # un singur element: punem data-t pe el
            new = f'<{m.group(1)}{m.group(2)} data-t="{key}">{m.group(3)}</{m.group(1)}>'
        else:  # mai multe elemente: le învelim într-un span
            new = f'<div class="tw" style="display:contents" data-t="{key}">{ro}</div>'
        html = html.replace(ro, new, 1)
        EN_ENTRIES[key] = en
    return html

top, bottom = add_t(top), add_t(bottom)

# ---------- scriptul ----------
js = lab[lab.index('<script>\n(() => {'):]
js = js[:js.rindex('</script>') + 9]
js = fix(js)
# ME vs me: textul se reface la schimbarea limbii (literele sunt <span> separate)
js = js.replace("  const big = document.getElementById('big');\n  const chars = [];",
"""  const big = document.getElementById('big');
  const BIG = { ro: big.innerHTML, en: 'ME vs me.<br />The only opponent<br />is yesterday’s you.' };
  let chars = [];
  function splitBig() {
    big.innerHTML = BIG[document.documentElement.lang === 'en' ? 'en' : 'ro']; chars = [];""")
js = js.replace("""  })(big);
  chars.slice(0, 9).forEach((c) => c.classList.add('v')); // „ME vs me.” în mov""",
"""  })(big);
    chars.slice(0, 9).forEach((c) => c.classList.add('v')); // „ME vs me.” în mov
  }
  splitBig();
  document.querySelectorAll('[data-lang]').forEach((b) => b.addEventListener('click', () => setTimeout(() => { splitBig(); manScroll(); }, 0)));""")
assert 'splitBig();' in js
# formularul: salvează emailul în Supabase (065_launch_waitlist.sql)
js = js.replace("""  document.getElementById('nform').addEventListener('submit', (e) => {
    if (e.submitter && e.submitter.value === 'ok') { dlg.querySelector('h3').textContent = 'Te-am notat!'; dlg.querySelector('p').textContent = 'Ne vedem pe 1 ianuarie.'; e.preventDefault(); setTimeout(() => dlg.close(), 1600); }
  });""",
"""  const SB = 'SUPABASE_URL', SBK = 'SUPABASE_KEY';
  const en = () => document.documentElement.lang === 'en';
  document.getElementById('nform').addEventListener('submit', async (e) => {
    if (!e.submitter || e.submitter.value !== 'ok') return;
    e.preventDefault();
    const inp = dlg.querySelector('input'), go = dlg.querySelector('.go'), email = inp.value.trim().toLowerCase();
    go.disabled = true;
    let ok = false;
    try {
      const r = await fetch(SB + '/rest/v1/launch_waitlist', { method: 'POST', headers: { apikey: SBK, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
        body: JSON.stringify({ email, lang: en() ? 'en' : 'ro', source: (new URLSearchParams(location.search).get('utm_source') || 'site').slice(0, 60) }) });
      ok = r.ok || r.status === 409; // 409 = era deja pe listă
    } catch (err) { ok = false; }
    go.disabled = false;
    if (ok) {
      try { window.umami && window.umami.track('notify_launch'); } catch (err) {}
      dlg.querySelector('h3').textContent = en() ? 'You are on the list!' : 'Te-am notat!';
      dlg.querySelector('p').textContent = en() ? 'See you on 1 January.' : 'Ne vedem pe 1 ianuarie.';
      inp.value = ''; setTimeout(() => dlg.close(), 1800);
    } else {
      dlg.querySelector('p').textContent = en() ? 'Something went wrong. Try again or write to contact@asfitness.ro.' : 'N-a mers. Încearcă din nou sau scrie-ne la contact@asfitness.ro.';
    }
  });""")
assert "launch_waitlist" in js
env = dict(l.split('=', 1) for l in (ROOT.parent / 'asfitness-app' / '.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
url, key = env['EXPO_PUBLIC_SUPABASE_URL'].strip(), env['EXPO_PUBLIC_SUPABASE_KEY'].strip()
assert key.startswith('sb_publishable'), 'doar cheia publică are voie pe site'
js = js.replace("'SUPABASE_URL'", repr(url)).replace("'SUPABASE_KEY'", repr(key))

# ---------- index.html ----------
hero_a = index.index('    <section class="hero">')
hero_b = index.index('    <section class="power"')
index = index[:hero_a] + '    <div class="nx">\n' + top + '    </div>\n\n' + index[hero_b:]
pre = index.index('    <section id="preturi">')
index = index[:pre] + '    <div class="nx">\n' + bottom + '    </div>\n\n' + index[pre:]
index = index.replace('<body>\n', '<body class="lock">\n  <div class="nx">\n' + loader + '  </div>\n', 1)
index = index.replace('  </style>\n</head>', css + '\n  </style>\n</head>', 1)
# sticky are nevoie de overflow: clip (hidden îl strică)
index = index.replace('-webkit-font-smoothing: antialiased; overflow-x: hidden; }', '-webkit-font-smoothing: antialiased; overflow-x: clip; }', 1)
assert 'overflow-x: clip' in index
index = index.replace('    html { scroll-behavior: smooth; }', '    html { scroll-behavior: smooth; overflow-x: clip; }', 1)
# traducerile EN
en_js = ''.join(f"\n      {k}: {repr(v)}," for k, v in EN_ENTRIES.items())
index = index.replace('    const EN = {', '    const EN = {' + en_js, 1)
# meniul: „Lansare” primul
index = index.replace('<a href="#povestea" data-t="nav_app">Aplicația</a>', '<a href="#launch" data-t="nav_launch">Lansare</a>\n        <a href="#povestea" data-t="nav_app">Aplicația</a>', 1)
index = index.replace('    const EN = {', "    const EN = {\n      nav_launch: 'Launch',", 1)
# scripturile la final
index = index.replace('</body>', '  <script src="lab/scan.js"></script>\n' + js + '\n</body>', 1)
(ROOT / 'index.html').write_text(index)
print('ok', len(EN_ENTRIES), 'traduceri')
