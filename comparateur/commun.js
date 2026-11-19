// Comparateur des programmes : fonctions communes, filtres, onglets
window.cpFmt = (x, d = 1) => (x == null || isNaN(x)) ? '—' : new Intl.NumberFormat('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
window.cpSigne = (x, d = 1) => (x == null || isNaN(x)) ? '—' : (x > 0 ? '+' : '') + cpFmt(x, d);
window.CP_SQ = 'Statu quo';
window.CP_FIN = 2060;
window.CP_VUES = ['ensemble', 'comparer', 'economie', 'emploi', 'population', 'menages', 'ecologie', 'fiabilite'];
window.cpParams = () => {
  const p = dash.params();
  return { scenario: p.scenario || 'Prudent', annee: Number(p.annee || 2037), programme: p.programme || null, groupe: p.groupe || null, vue: CP_VUES.includes(p.vue) ? p.vue : 'ensemble' };
};
window.cpProgrammes = () => {
  const d = dash.data('traj');
  if (d.status !== 'ok') return [];
  return [...new Set(d.data.map((r) => r.programme))];
};
window.cpProgDetail = () => {
  const progs = cpProgrammes().filter((x) => x !== CP_SQ);
  const p = cpParams().programme;
  return progs.includes(p) ? p : (progs[0] || null);
};
window.cpCouleur = (prog) => {
  if (prog === CP_SQ) return 'var(--cds-chart-muted)';
  const i = cpProgrammes().filter((x) => x !== CP_SQ).indexOf(prog);
  return dash.colors[Math.max(0, i) % dash.colors.length];
};
// année la plus proche dans une liste (années calculées de la micro, de la pyramide…)
window.cpProche = (liste) => {
  const a = cpParams().annee;
  return liste.reduce((b, x) => (Math.abs(x - a) < Math.abs(b - a) ? x : b));
};
window.cpPret = (el, d) => {
  if (d.status !== 'ok') {
    el.replaceChildren();
    el.classList.toggle('failed', d.status === 'error' || d.status === 'connect');
    el.classList.toggle('dash-skeleton', d.status === 'loading');
    return false;
  }
  el.classList.remove('failed', 'dash-skeleton');
  return true;
};
// valeur d'une ligne (programme, scénario, année) d'un jeu de données ; marque la source
window.cpValeur = (el, source, prog, champ, o = {}) => {
  const d = dash.data(source);
  const p = cpParams();
  const an = o.annee ?? p.annee;
  if (d.status !== 'ok' || !prog) { el.textContent = '—'; return null; }
  el.dataset.where = `programme=${encodeURIComponent(prog)}&scenario=${encodeURIComponent(p.scenario)}&annee=${an}`;
  const r = d.data.find((x) => x.programme === prog && x.scenario === p.scenario && Number(x.annee) === an);
  const v = r ? Number(r[champ]) : null;
  el.textContent = r ? (o.signe ? cpSigne(v, o.d ?? 1) : cpFmt(v, o.d ?? 1)) + (o.suffixe || '') : (o.absent || '—');
  return v;
};
// colore une valeur de tuile par rapport au statu quo : sens 'bas' (plus bas = mieux) ou 'haut'
window.cpClasse = (el, v, ref, sens, seuil = 0.05) => {
  el.classList.remove('bon', 'mauvais');
  if (v == null || ref == null || isNaN(v) || isNaN(ref)) return;
  const e = sens === 'bas' ? ref - v : v - ref;
  if (e > seuil) el.classList.add('bon');
  else if (e < -seuil) el.classList.add('mauvais');
};
window.cpLigneTraj = (prog, an) => {
  const d = dash.data('traj');
  const p = cpParams();
  if (d.status !== 'ok') return null;
  return d.data.find((x) => x.programme === prog && x.scenario === p.scenario && Number(x.annee) === (an ?? p.annee)) || null;
};

// séries d'un jeu de données, une par programme, pour le scénario choisi
window.cpSerie = (d, prog, col, o = {}) => ({
  nom: prog + (o.suffixe || ''), prog, couleur: cpCouleur(prog), tirets: o.tirets ?? (prog === CP_SQ),
  points: d.data.filter((r) => r.programme === prog && r.scenario === cpParams().scenario && Number(r.annee) <= CP_FIN
    && Number(r.annee) >= (o.debut || 0) && r[col] !== '' && r[col] != null)
    .map((r) => [Number(r.annee), Number(r[col])]),
});
window.cpParProgramme = (source, col, unite, zero, sens, o = {}) => (el) => {
  const d = dash.data(source);
  if (!cpPret(el, d)) return;
  cpLignes(el, cpProgrammes().map((prog) => cpSerie(d, prog, col, o)), unite, zero, sens, o.dec);
};

// graphique en lignes : series = [{nom, prog, couleur, tirets, points: [[annee, valeur]]}]
// sens : 'bas' (plus bas = mieux), 'haut' (plus haut = mieux) ou null (pas de classement)
window.cpLignes = (el, series, unite, zero, sens, dec = 1) => {
  el.replaceChildren();
  const valeur = (s, an) => { const pt = s.points.find((p) => p[0] === an); return pt ? pt[1] : null; };
  const ordre = (liste, an) => (!sens ? liste : [...liste].sort((a, b) => {
    if (!!a.horsRang !== !!b.horsRang) return a.horsRang ? 1 : -1;
    const va = valeur(a, an), vb = valeur(b, an);
    if (va == null || vb == null) return va == null ? 1 : -1;
    return sens === 'bas' ? va - vb : vb - va;
  }));
  const W = Math.max(280, el.clientWidth), H = 260, B = 24;
  const tous = series.flatMap((s) => s.points);
  if (!tous.length) return;
  const x = d3.scaleLinear(d3.extent(tous, (p) => p[0]), [0, 1]);
  const ext = d3.extent(tous, (p) => p[1]);
  const y = d3.scaleLinear([zero ? Math.min(0, ext[0]) : ext[0], Math.max(zero ? 0 : ext[1], ext[1])], [H - B, 10]).nice();
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
    .attr('aria-label', `Courbes par programme, ${cpParams().scenario.toLowerCase()}`);
  const tickDec = (y.domain()[1] - y.domain()[0]) < 5 ? 1 : 0;
  const gy = svg.append('g').call(d3.axisLeft(y).ticks(5).tickFormat((v) => cpFmt(v, tickDec)));
  gy.attr('font-size', null).attr('font-family', null);
  let ml = 0; gy.selectAll('text').each(function () { ml = Math.max(ml, this.getComputedTextLength()); });
  ml += 10;
  const mr = 14;
  x.range([ml, W - mr]);
  gy.attr('transform', `translate(${ml},0)`);
  gy.select('.domain').remove();
  gy.selectAll('line').attr('x2', W - ml - mr).style('stroke', 'var(--cds-chart-grid)');
  gy.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  const gx = svg.append('g').attr('transform', `translate(0,${H - B})`).call(d3.axisBottom(x).ticks(Math.max(2, Math.floor(W / 90))).tickFormat(d3.format('d')));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  if (y.domain()[0] < 0 && y.domain()[1] > 0) svg.append('line').attr('x1', ml).attr('x2', W - mr).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-reference)');
  const ligne = d3.line().x((p) => x(p[0])).y((p) => y(p[1]));
  const prog = cpProgDetail();
  for (const s of series) {
    s.trace = svg.append('path').attr('d', ligne(s.points)).attr('fill', 'none').style('stroke', s.couleur)
      .attr('stroke-width', s.prog === prog ? 3 : 1.6).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round')
      .attr('stroke-dasharray', typeof s.tirets === 'string' ? s.tirets : (s.tirets ? '5 4' : null));
    if (s.points.length === 1 || s.marques) {
      svg.append('g').selectAll('circle').data(s.points).join('circle').attr('cx', (p) => x(p[0])).attr('cy', (p) => y(p[1])).attr('r', 3).style('fill', s.couleur);
    }
  }
  const leg = document.createElement('div');
  leg.className = 'legend legende-tri';
  el.prepend(leg);
  const an0 = cpProche([...new Set(tous.map((p) => p[0]))]);
  const surligne = (pr) => { for (const s of series) s.trace.style('opacity', pr == null || s.prog === pr ? 1 : 0.12); };
  if (sens) {
    const t = document.createElement('span');
    t.className = 'tri-titre';
    t.textContent = `En ${an0}, du meilleur au moins bon (${sens === 'bas' ? 'plus bas' : 'plus haut'} = mieux) :`;
    leg.append(t);
  }
  let rang = 0;
  for (const s of (sens ? ordre(series, an0) : series)) {
    const sp = document.createElement('span');
    sp.style.setProperty('--sw', s.couleur);
    if (s.tirets) sp.style.setProperty('--trait', typeof s.tirets === 'string' ? 'dotted' : 'dashed');
    const v = sens ? valeur(s, an0) : null;
    const num = sens && !s.horsRang && s.prog !== CP_SQ ? `${++rang}. ` : '';
    if (s.prog === CP_SQ) sp.className = 'sq';
    if (s.prog === prog) sp.classList.add('choisi');
    sp.textContent = num + s.nom + (sens && v != null ? ` : ${cpFmt(v, dec)}${unite}` : '');
    sp.addEventListener('pointerenter', () => surligne(s.prog));
    sp.addEventListener('pointerleave', () => surligne(null));
    leg.append(sp);
  }
  const tip = d3.select(el).append('div').attr('class', 'tip').style('display', 'none');
  const regle = svg.append('line').attr('y1', 10).attr('y2', H - B).style('stroke', 'var(--cds-chart-axis)').style('display', 'none');
  const annees = [...new Set(tous.map((p) => p[0]))].sort((a, b) => a - b);
  const px = annees.map((a) => x(a));
  svg.append('rect').attr('x', ml).attr('y', 0).attr('width', W - ml - mr).attr('height', H - B).attr('fill', 'transparent')
    .on('pointermove', (ev) => {
      const [mx] = d3.pointer(ev);
      const an = annees[Math.max(0, Math.min(annees.length - 1, d3.bisectCenter(px, mx)))];
      regle.style('display', null).attr('x1', x(an)).attr('x2', x(an));
      tip.style('display', null).selectAll('*').remove();
      tip.append('div').attr('class', 't').text(an);
      for (const s of ordre(series, an)) {
        const pt = s.points.find((p) => p[0] === an);
        if (!pt) continue;
        const l = tip.append('div');
        l.append('span').style('display', 'inline-block').style('width', '.6rem').style('height', '.6rem').style('margin-right', '.35rem').style('background', s.couleur);
        l.append('span').text(`${s.nom} : ${cpFmt(pt[1], dec)}${unite}`);
      }
      const bw = el.clientWidth, pos = x(an) / W * bw, tw = tip.node().offsetWidth;
      tip.style('left', `${Math.max(0, Math.min(bw - tw, pos + 10 + tw > bw ? pos - tw - 10 : pos + 10))}px`).style('top', `${leg.offsetHeight + 8}px`);
    })
    .on('pointerleave', () => { tip.style('display', 'none'); regle.style('display', 'none'); });
};

// barres horizontales autour de zéro : rows = [{nom, v, lab}] ; bon : 'positif' ou 'negatif'
window.cpBarres = (el, rows, o = {}) => {
  el.replaceChildren();
  if (!rows.length) return;
  const W = Math.max(280, el.clientWidth), pas = 28, H = rows.length * pas + 28;
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img').attr('aria-label', o.aria || 'Barres');
  const mesure = svg.append('g').style('font-size', 'var(--cds-font-size-caption)');
  let ml = 0;
  mesure.selectAll('text').data(rows).join('text').text((r) => r.nom).each(function () { ml = Math.max(ml, this.getComputedTextLength()); });
  mesure.remove();
  ml = Math.min(ml + 12, W * 0.45);
  const essai = svg.append('text').style('font-size', 'var(--cds-font-size-caption)').text(rows.reduce((a, b) => (a.lab.length > b.lab.length ? a : b)).lab);
  const lw = Math.min(essai.node().getComputedTextLength() + 8, W * 0.3);
  essai.remove();
  const m = d3.max(rows, (r) => Math.abs(r.v)) || 1;
  const x = d3.scaleLinear([-m, m], [ml + lw, W - lw]);
  svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', 0).attr('y2', H - 20).style('stroke', 'var(--cds-chart-reference)');
  const bon = (r) => (o.bon === 'negatif' ? r.v <= 0 : r.v >= 0);
  const g = svg.selectAll('g.ligne').data(rows).join('g').attr('class', 'ligne').attr('transform', (r, i) => `translate(0,${i * pas})`);
  if (o.clic) g.style('cursor', 'pointer').on('click', (ev, r) => o.clic(r));
  g.append('rect').attr('x', 0).attr('y', 0).attr('width', W).attr('height', pas).attr('fill', 'transparent');
  g.append('text').attr('x', 0).attr('y', pas / 2).attr('dy', '0.35em').text((r) => r.nom)
    .style('fill', (r) => (o.attenue && o.attenue(r) ? 'var(--color-fg-muted)' : 'var(--color-fg)')).style('font-size', 'var(--cds-font-size-caption)');
  g.append('rect').attr('x', (r) => Math.min(x(0), x(r.v))).attr('y', 5).attr('height', pas - 10)
    .attr('width', (r) => Math.max(1, Math.abs(x(r.v) - x(0)))).attr('rx', 3)
    .style('fill', (r) => (bon(r) ? dash.colors[0] : 'var(--cds-chart-status-critical)'))
    .style('opacity', (r) => (o.attenue && o.attenue(r) ? 0.35 : 1));
  g.append('text').attr('x', (r) => (r.v >= 0 ? x(r.v) + 4 : x(r.v) - 4)).attr('y', pas / 2).attr('dy', '0.35em')
    .attr('text-anchor', (r) => (r.v >= 0 ? 'start' : 'end')).text((r) => r.lab)
    .style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)').style('font-variant-numeric', 'tabular-nums');
  const gx = svg.append('g').attr('transform', `translate(0,${H - 20})`).call(d3.axisBottom(x).ticks(5).tickFormat((v) => cpFmt(v, o.dec ?? 1)));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
};

// lignes de tableau : cols = [[texte, classe]]
window.cpLigneTableau = (tb, cle, cols, classe) => {
  const tr = document.createElement('tr');
  tr.dataset.key = cle;
  if (classe) tr.className = classe;
  for (const [txt, c] of cols) {
    const td = document.createElement('td');
    td.textContent = txt;
    if (c) td.className = c;
    tr.append(td);
  }
  tb.append(tr);
};
window.cpComparer = (v, ref, sens, seuil = 0.05) => {
  if (v == null || ref == null || isNaN(v) || isNaN(ref)) return '';
  const e = sens === 'bas' ? ref - v : v - ref;
  return e > seuil ? 'bon' : (e < -seuil ? 'mauvais' : '');
};

// filtres
for (const b of document.querySelectorAll('.cp .seg button[data-scen]')) b.addEventListener('click', () => dash.setParams({ scenario: b.dataset.scen }));
for (const s of document.querySelectorAll('.cp .f-annee')) s.addEventListener('change', () => dash.setParams({ annee: Number(s.value) }));
// onglets
const cpOuvrir = (vue) => { dash.setParams({ vue }); dash.setLink(vue); };
for (const b of document.querySelectorAll('.cp [data-vue]')) b.addEventListener('click', () => cpOuvrir(b.dataset.vue));
for (const a of document.querySelectorAll('.cp a[data-aller]')) a.addEventListener('click', (ev) => { ev.preventDefault(); cpOuvrir(a.dataset.aller); });
{
  const h = (location.hash || '').replace('#', '');
  if (CP_VUES.includes(h)) dash.setParams({ vue: h });
}
window.cpImpression = false;
dash.onData(() => {
  const p = cpParams();
  for (const b of document.querySelectorAll('.cp .seg button[data-scen]')) b.setAttribute('aria-pressed', String(b.dataset.scen === p.scenario));
  for (const s of document.querySelectorAll('.cp .f-annee')) s.value = String(p.annee);
  for (const b of document.querySelectorAll('.cp [data-vue]')) b.setAttribute('aria-selected', String(b.dataset.vue === p.vue));
  for (const s of document.querySelectorAll('.cp section.vue')) s.hidden = !cpImpression && s.id !== p.vue;
  const prog = cpProgDetail();
  for (const el of document.querySelectorAll('.cp .resume-prog')) el.hidden = el.dataset.prog !== prog;
});
window.addEventListener('beforeprint', () => { cpImpression = true; for (const s of document.querySelectorAll('.cp section.vue')) s.hidden = false; });
window.addEventListener('afterprint', () => {
  cpImpression = false;
  const v = cpParams().vue;
  for (const s of document.querySelectorAll('.cp section.vue')) s.hidden = s.id !== v;
});

// mots communs
dash.draw('l_annee', (el) => { el.textContent = String(cpParams().annee); });
dash.draw('l_scen', (el) => { el.textContent = cpParams().scenario.toLowerCase(); });
dash.draw('l_prog', (el) => { el.textContent = cpProgDetail() || '—'; });
dash.draw('f_prog', (sel) => {
  const progs = cpProgrammes().filter((x) => x !== CP_SQ);
  sel.replaceChildren(...progs.map((x) => new Option(x, x)));
  sel.value = cpProgDetail() || '';
  sel.onchange = () => dash.setParams({ programme: sel.value || null, groupe: null });
});
dash.draw('l_def_prog', (el) => cpValeur(el, 'traj', cpProgDetail(), 'deficit', { suffixe: ' %' }));
dash.draw('l_def_sq', (el) => cpValeur(el, 'traj', CP_SQ, 'deficit', { suffixe: ' %' }));
dash.draw('l_esp', (el) => {
  const v = cpValeur(el, 'traj', cpProgDetail(), 'ecart_solde_primaire_pib', { d: 2, signe: true });
  cpClasse(el, v, 0, 'haut');
});
