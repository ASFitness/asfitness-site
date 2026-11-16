
(() => {
  // Etichetele: x, y = punctul de pe corp (0–1 din poză); side = partea pe care stă textul.
  const DATA = {
    m: { img: '../img/scan/m.webp', name: 'Atlet 01', labels: [
      { x: .47, y: .09, side: 'l', k: 'Somn', v: '7h 40', s: 'Refacere bună, poți trage tare azi' },
      { x: .56, y: .24, side: 'r', k: 'Pregătire', v: '82%', s: 'Din WHOOP + cum te simți dimineața' },
      { x: .30, y: .40, side: 'l', k: 'Mușchii săptămânii', v: 'Piept · Spate', s: 'Ce ai lucrat și ce mai trebuie' },
      { x: .53, y: .42, side: 'r', k: 'Nutriție', v: '2.450 kcal', s: 'Proteine 160 g, după antrenamentul zilei' },
      { x: .40, y: .66, side: 'l', k: 'Încărcare', v: 'Optimă', s: 'Raport efort acut / cronic 1,1' },
      { x: .63, y: .80, side: 'r', k: 'Hidratare', v: '2,8 L', s: 'Calculată din testul de transpirație' },
    ]},
    f: { img: '../img/scan/f.webp', name: 'Atlet 02', labels: [
      { x: .49, y: .10, side: 'l', k: 'Somn', v: '8h 05', s: 'Refacere foarte bună' },
      { x: .55, y: .25, side: 'r', k: 'Pregătire', v: '76%', s: 'Din WHOOP + cum te simți dimineața' },
      { x: .31, y: .36, side: 'l', k: 'Mușchii săptămânii', v: 'Fesieri · Spate', s: 'Ce ai lucrat și ce mai trebuie' },
      { x: .50, y: .42, side: 'r', k: 'Ciclu', v: 'Ziua 9', s: 'Normalul tău: antrenament și mese adaptate', hot: true },
      { x: .60, y: .60, side: 'r', k: 'Nutriție', v: '1.950 kcal', s: 'Proteine 120 g, după antrenamentul zilei' },
      { x: .39, y: .80, side: 'l', k: 'Încărcare', v: 'Optimă', s: 'Raport efort acut / cronic 1,0' },
    ]},
  };

  const hud = document.getElementById('hud'), body = document.getElementById('body'), cv = document.getElementById('cv');
  const ctx = cv.getContext('2d'), svg = document.getElementById('lines'), labsEl = document.getElementById('labs');
  const small = matchMedia('(max-width: 760px)').matches;
  const GW = small ? 104 : 150, GH = Math.round(GW * 1.5);
  let cw = 0, ch = 0, dpr = Math.min(devicePixelRatio || 1, 2);
  const sets = {};

  // Din poză facem puncte: doar pixelii luminoși (fundalul e negru).
  function sample(src) {
    return new Promise((res) => {
      const im = new Image();
      im.onload = () => {
        const c = document.createElement('canvas'); c.width = GW; c.height = GH;
        const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(im, 0, 0, GW, GH);
        const d = g.getImageData(0, 0, GW, GH).data, pts = [];
        for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) {
          const i = (y * GW + x) * 4, L = (d[i] * .3 + d[i + 1] * .55 + d[i + 2] * .15) / 255;
          const purple = d[i + 2] > d[i + 1] * 1.4 && d[i + 2] > 60;
          if (L > .045 || purple) pts.push({ x: (x + .5) / GW, y: (y + .5) / GH, b: Math.min(1, Math.max(Math.pow(L, .6), purple ? .45 : 0) * 1.15) });
        }
        res(pts);
      };
      im.src = src;
    });
  }

  // Particule care pot trece dintr-un corp în altul.
  let P = [], cur = 'm', morph = 1, morphFrom = null;
  function pairTo(target) {
    const T = sets[target].slice().sort((a, b) => a.y - b.y + (Math.random() - .5) * .02);
    while (P.length < T.length) { const s = P[(Math.random() * P.length) | 0] || T[0]; P.push({ ...s, fx: s.x, fy: s.y }); }
    const src = P.slice().sort((a, b) => a.y - b.y);
    P = src.map((p, i) => {
      const t = T[i < T.length ? i : (Math.random() * T.length) | 0];
      return { x: p.x, y: p.y, b: p.b, fx: p.x, fy: p.y, fb: p.b, tx: t.x, ty: t.y, tb: t.b, j: Math.random(), ph: Math.random() * 6.28, dead: i >= T.length };
    });
  }

  function size() {
    const r = hud.getBoundingClientRect();
    ch = Math.round(small ? Math.min(440, r.width * 1.2) : r.height * .9); cw = Math.round(ch / 1.5);
    cv.width = cw * dpr; cv.height = ch * dpr; cv.style.width = cw + 'px'; cv.style.height = ch + 'px';
    body.style.marginLeft = -cw / 2 + 'px'; body.style.marginTop = (small ? -r.height / 2 + 120 : -ch / 2 + 8) + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    placeLabels();
  }

  // Etichete + linii
  let labEls = [];
  function buildLabels() {
    labsEl.innerHTML = ''; svg.innerHTML = '';
    labEls = [];
    DATA[cur].labels.forEach((L, idx) => {
      const el = document.createElement('div');
      el.className = 'lab ' + L.side + (L.hot ? ' hot' : '');
      el.innerHTML = `<div class="k">${small ? '0' + (labEls.length + 1) + ' · ' : ''}${L.k}</div><div class="v">${L.v}</div><div class="s">${L.s}</div>`;
      labsEl.appendChild(el);
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.innerHTML = '<path/><circle r="3"/><circle class="ring" r="5"/>' + (small ? `<text font-size="10" fill="#EDE9FE" font-family="JetBrains Mono">0${idx + 1}</text>` : '');
      svg.appendChild(g);
      labEls.push({ L, el, g, shown: false });
    });
    placeLabels();
  }
  function placeLabels() {
    const hr = hud.getBoundingClientRect(), br = cv.getBoundingClientRect();
    const ox = br.left - hr.left, oy = br.top - hr.top;
    const bottom = { l: 0, r: 0 };
    labEls.slice().sort((a, b) => a.L.y - b.L.y).forEach(({ L, el, g }) => {
      const ax = ox + L.x * cw, ay = oy + L.y * ch;
      if (small) {
        const i = DATA[cur].labels.indexOf(L), colW = (hr.width - 56) / 2;
        el.style.width = colW + 'px'; el.style.left = 28 + (i % 2) * colW + 'px'; el.style.top = oy + ch + 22 + Math.floor(i / 2) * 62 + 'px';
        g.querySelector('path').setAttribute('d', '');
        g.querySelectorAll('circle').forEach((c) => { c.setAttribute('cx', ax); c.setAttribute('cy', ay); });
        const tx = g.querySelector('text'); if (tx) { tx.setAttribute('x', ax + (L.side === 'l' ? -22 : 8)); tx.setAttribute('y', ay + 3.5); }
        return;
      }
      const w = el.offsetWidth || 200, h = el.offsetHeight || 60;
      const gap = small ? 8 : 64;
      const lx = L.side === 'l' ? Math.max(small ? 10 : 40, ox - gap - w) : Math.min(hr.width - w - (small ? 10 : 40), ox + cw + gap);
      const ly = Math.max(70, bottom[L.side] + 12, Math.min(hr.height - h - 40, ay - h / 2));
      bottom[L.side] = ly + h;
      el.style.left = lx + 'px'; el.style.top = ly + 'px';
      const ex = L.side === 'l' ? lx + w + 10 : lx - 10, ey = ly + h / 2;
      const kx = L.side === 'l' ? ax - 26 : ax + 26;
      g.querySelector('path').setAttribute('d', `M${ax},${ay} L${kx},${ey} L${ex},${ey}`);
      g.querySelectorAll('circle').forEach((c) => { c.setAttribute('cx', ax); c.setAttribute('cy', ay); });
    });
  }

  // Linia de scanare
  let scanY = -0.1, revealY = -0.1, scanning = true, t0 = performance.now();
  function restartScan() { scanY = -0.08; revealY = -0.08; scanning = true; labEls.forEach((o) => { o.shown = false; o.el.classList.remove('on'); o.g.classList.remove('on'); }); }

  const LEVELS = 9;
  const col = (b) => { // mov închis → lavandă → alb
    const a = [76, 29, 149], m = [167, 139, 250], w = [245, 243, 255];
    const lerp = (p, q, t) => p.map((v, i) => Math.round(v + (q[i] - v) * t));
    return b < .5 ? lerp(a, m, b * 2) : lerp(m, w, (b - .5) * 2);
  };
  const COLS = Array.from({ length: LEVELS }, (_, i) => `rgb(${col((i + .5) / LEVELS).join(',')})`);

  let last = performance.now(), glitch = { y: -1, h: 0, dx: 0, until: 0 };
  let visible = false, everSeen = false;
  new IntersectionObserver(([e]) => {
    visible = e.isIntersecting;
    if (visible && !everSeen) { everSeen = true; restartScan(); }
  }, { threshold: .25 }).observe(hud);
  function frame(now) {
    const dt = Math.min(50, now - last); last = now;
    if (!visible) { requestAnimationFrame(frame); return; }
    const t = now / 1000;
    // morph între corpuri
    if (morph < 1) {
      morph = Math.min(1, morph + dt / 1500);
      const e = morph < .5 ? 4 * morph ** 3 : 1 - (-2 * morph + 2) ** 3 / 2;
      for (const p of P) {
        const sc = Math.sin(Math.PI * e) * (.04 + p.j * .1);
        p.x = p.fx + (p.tx - p.fx) * e + Math.cos(p.ph + t) * sc;
        p.y = p.fy + (p.ty - p.fy) * e + Math.sin(p.ph * 1.3 + t) * sc * .6;
        p.b = p.fb + (p.tb - p.fb) * e;
      }
      if (morph === 1) { P = P.filter((p) => !p.dead); P.forEach((p) => { p.x = p.tx; p.y = p.ty; p.b = p.tb; }); }
    }
    // scanare
    scanY += dt / (scanning ? 2600 : 4200);
    if (scanning) revealY = scanY;
    if (scanY > 1.1) { if (scanning) scanning = false; scanY = -0.15; }
    document.getElementById('pct').textContent = Math.round(Math.max(0, Math.min(1, revealY)) * 100) + '%';
    labEls.forEach((o) => { if (!o.shown && revealY > o.L.y) { o.shown = true; o.el.classList.add('on'); o.g.classList.add('on'); } });
    // glitch ocazional
    if (now > glitch.until && Math.random() < .012) glitch = { y: Math.random(), h: .01 + Math.random() * .03, dx: (Math.random() - .5) * .05, until: now + 90 + Math.random() * 120 };
    const gOn = now < glitch.until;

    ctx.clearRect(0, 0, cw, ch);
    const cell = cw / GW;
    const paths = Array.from({ length: LEVELS }, () => new Path2D());
    const hi = new Path2D();
    for (const p of P) {
      if (p.y > revealY + .005 && morph === 1) continue;
      const fl = .75 + .25 * Math.sin(t * 3 + p.ph * 7);
      let x = p.x, y = p.y;
      if (gOn && y > glitch.y && y < glitch.y + glitch.h) x += glitch.dx;
      const d = Math.abs(y - scanY);
      const s = cell * (.32 + p.b * .72) * fl;
      const X = x * cw - s / 2, Y = y * ch - s / 2;
      if (d < .012) { hi.rect(X - .4, Y - .4, s + .8, s + .8); continue; }
      paths[Math.min(LEVELS - 1, (p.b * LEVELS) | 0)].rect(X, Y, s, s);
    }
    for (let i = 0; i < LEVELS; i++) { ctx.globalAlpha = .45 + .55 * (i / LEVELS); ctx.fillStyle = COLS[i]; ctx.fill(paths[i]); }
    ctx.globalAlpha = 1; ctx.fillStyle = '#fff'; ctx.shadowColor = '#A78BFA'; ctx.shadowBlur = 10; ctx.fill(hi); ctx.shadowBlur = 0;
    // linia
    if (scanY > -0.05 && scanY < 1.05) {
      const ly = scanY * ch, gr = ctx.createLinearGradient(0, ly - 40, 0, ly + 2);
      gr.addColorStop(0, 'rgba(167,139,250,0)'); gr.addColorStop(1, 'rgba(167,139,250,.22)');
      ctx.fillStyle = gr; ctx.fillRect(-20, ly - 40, cw + 40, 42);
      ctx.fillStyle = 'rgba(237,233,254,.85)'; ctx.fillRect(-20, ly, cw + 40, 1.2);
    }
    if (Math.random() < .05) document.getElementById('hex').textContent = 'ASF-' + Math.random().toString(36).slice(2, 6).toUpperCase();
    requestAnimationFrame(frame);
  }

  // Comutare băiat / fată
  let auto = true, autoTimer;
  function show(k, user) {
    if (user) { auto = false; clearInterval(autoTimer); }
    if (k === cur || morph < 1) return;
    cur = k; morph = 0; pairTo(k);
    document.getElementById('bm').classList.toggle('on', k === 'm');
    document.getElementById('bf').classList.toggle('on', k === 'f');
    document.getElementById('who').textContent = DATA[k].name;
    buildLabels(); restartScan(); revealY = 1.2; scanning = true; scanY = -0.08;
    labEls.forEach((o) => { o.shown = false; });
    setTimeout(() => { revealY = -0.08; scanY = -0.08; }, 10);
  }
  document.getElementById('bm').onclick = () => show('m', true);
  document.getElementById('bf').onclick = () => show('f', true);

  // Înclinare după mouse (doar pe calculator)
  if (!small) hud.addEventListener('mousemove', (e) => {
    const r = hud.getBoundingClientRect(), nx = (e.clientX - r.left) / r.width - .5, ny = (e.clientY - r.top) / r.height - .5;
    body.style.transform = `rotateY(${nx * 14}deg) rotateX(${-ny * 7}deg)`;
  });
  hud.addEventListener('mouseleave', () => { body.style.transform = ''; });

  Promise.all([sample(DATA.m.img), sample(DATA.f.img)]).then(([m, f]) => {
    sets.m = m; sets.f = f;
    P = m.map((p) => ({ ...p, j: Math.random(), ph: Math.random() * 6.28 }));
    size(); buildLabels(); restartScan();
    addEventListener('resize', size);
    autoTimer = setInterval(() => { if (auto && visible) show(cur === 'm' ? 'f' : 'm'); }, 9000);
    requestAnimationFrame(frame);
  });
})();
