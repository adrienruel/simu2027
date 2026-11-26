// Fiabilité : annonces contre chiffrage, variantes de la dette, incertitude, lectures à valider
dash.draw('t_annonces', (tb) => {
  const d = dash.data('annonces');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams();
  const rows = d.data.filter((r) => r.scenario === p.scenario).sort((a, b) => Number(b.ecart_pib) - Number(a.ecart_pib));
  for (const r of rows) {
    cpLigneTableau(tb, r.cle, [[r.programme], [r.annonce], [cpFmt(Number(r.annonce_md), 0)], [cpFmt(Number(r.modele_md), 1)], [cpFmt(Number(r.ecart_md), 1)],
      [cpFmt(Number(r.ecart_pib), 2)], [cpFmt(Number(r.effet_net_pib), 2)], [cpFmt(Number(r.deficit), 1) + ' %'], [cpFmt(Number(r.deficit_si_tenue), 1) + ' %']],
    r.programme === cpProgDetail() ? 'choisi' : '');
  }
});

// variantes communes de la dette
const VARIANTES_DETTE = ['centrale', 'sans_prime_dette', 'taux_long_3_3', 'croissance_2027_2028'];
dash.calc('variantes_tab', {
  inputs: ['dette_variantes'],
  title: 'Variantes de la dette par programme',
  description: 'Déficit et écart de déficit au statu quo de la même variante, par programme, scénario et année, dans le calcul publié et les trois variantes communes.',
  fn: (dette_variantes) => {
    const par = new Map();
    for (const r of dette_variantes) {
      const cle = r.programme + '|' + r.scenario + '|' + r.annee;
      const x = par.get(cle) || { cle, programme: r.programme, scenario: r.scenario, annee: r.annee };
      x['deficit_' + r.variante] = Number(r.deficit);
      x['ecart_' + r.variante] = Number(r.ecart_deficit_statu_quo);
      par.set(cle, x);
    }
    return [...par.values()];
  },
});
dash.draw('v_annee2', (el) => { el.textContent = String(cpProche([2032, 2037, 2050])); });
const varSq = (el, v) => cpValeurCle(el, 'variantes_tab', CP_SQ, 'deficit_' + v, { annee: cpProche([2032, 2037, 2050]) });
dash.draw('v_sq_c', (el) => varSq(el, 'centrale'));
dash.draw('v_sq_p', (el) => varSq(el, 'sans_prime_dette'));
dash.draw('v_sq_t', (el) => varSq(el, 'taux_long_3_3'));
dash.draw('v_sq_g', (el) => varSq(el, 'croissance_2027_2028'));
dash.draw('t_variantes', (tb) => {
  const d = dash.data('variantes_tab');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams(), an = cpProche([2032, 2037, 2050]);
  const rows = d.data.filter((r) => r.scenario === p.scenario && Number(r.annee) === an && r.programme !== CP_SQ).sort((a, b) => a.ecart_centrale - b.ecart_centrale);
  for (const r of rows) {
    cpLigneTableau(tb, r.cle, [[r.programme], [cpFmt(r.deficit_centrale, 1)], ...VARIANTES_DETTE.map((v) => [cpSigne(r['ecart_' + v], 2), cpComparer(r['ecart_' + v], 0, 'bas')])],
      r.programme === cpProgDetail() ? 'choisi' : '');
  }
});

// incertitude : fourchettes à hypothèses indépendantes (rho 0) et liées (rho 1)
dash.calc('incertitude_tab', {
  inputs: ['incertitude'],
  title: 'Fourchettes par programme',
  description: 'Centiles 10, 50 et 90 de chaque grandeur, hypothèses indépendantes (rho 0) et liées (rho 1), et part des tirages où le déficit est sous celui du statu quo.',
  fn: (incertitude) => {
    const par = new Map();
    for (const r of incertitude) {
      if (r.rho !== '0' && r.rho !== '1') continue;
      const cle = r.dossier + '|' + r.grandeur + '|' + r.annee;
      const x = par.get(cle) || { cle, programme: r.programme, dossier: r.dossier, grandeur: r.grandeur, annee: r.annee, hypotheses: '' };
      const k = r.rho === '0' ? 'rho0' : 'rho1';
      x['p10_' + k] = Number(r.p10); x['p50_' + k] = Number(r.p50); x['p90_' + k] = Number(r.p90);
      x['proba_' + k] = r.proba_mieux_que_statu_quo === '' || r.proba_mieux_que_statu_quo == null ? null : Number(r.proba_mieux_que_statu_quo) * 100;
      if (k === 'rho1' && r.hypotheses_deficit_2037) x.hypotheses = r.hypotheses_deficit_2037;
      if (k === 'rho1') x.ex_aequo = r.ex_aequo || '';
      par.set(cle, x);
    }
    return [...par.values()].filter((x) => x.p50_rho0 != null && x.p50_rho1 != null);
  },
});
window.cpInc = () => {
  const p = dash.params();
  return { annee: String(p.inc_annee || 2037), grandeur: p.inc_grandeur || 'deficit' };
};
const INC_UNITE = { deficit: ' %', dette_pib: ' %', chomage: ' %' };
const INC_DEC = { deficit: 1, dette_pib: 0, chomage: 1 };
for (const b of document.querySelectorAll('.cp [data-inc-annee]')) b.addEventListener('click', () => dash.setParams({ inc_annee: Number(b.dataset.incAnnee) }));
for (const b of document.querySelectorAll('.cp [data-inc-grandeur]')) b.addEventListener('click', () => dash.setParams({ inc_grandeur: b.dataset.incGrandeur }));
dash.onData(() => {
  const p = cpInc();
  for (const b of document.querySelectorAll('.cp [data-inc-annee]')) b.setAttribute('aria-pressed', String(b.dataset.incAnnee === p.annee));
  for (const b of document.querySelectorAll('.cp [data-inc-grandeur]')) b.setAttribute('aria-pressed', String(b.dataset.incGrandeur === p.grandeur));
  for (const s of document.querySelectorAll('.cp .leg-inc .etroite')) s.style.setProperty('--sw', dash.colors[0]);
});
const incLignes = () => {
  const d = dash.data('incertitude_tab');
  if (d.status !== 'ok') return null;
  const p = cpInc();
  return d.data.filter((r) => r.grandeur === p.grandeur && r.annee === p.annee);
};
dash.draw('i_annee', (el) => { el.textContent = cpInc().annee; });
const incSq = (el, champ) => cpValeurCle(el, 'incertitude_tab', CP_SQ, champ, { cle: `statu_quo|deficit|${cpInc().annee}` });
dash.draw('i_sq_bas', (el) => incSq(el, 'p10_rho1'));
dash.draw('i_sq_haut', (el) => incSq(el, 'p90_rho1'));
dash.draw('i_sq_bas0', (el) => incSq(el, 'p10_rho0'));
dash.draw('i_sq_haut0', (el) => incSq(el, 'p90_rho0'));
// programmes que les tirages ne départagent pas : « ex æquo » après le nom (26/11/2026)
const incNom = (r) => (r.ex_aequo ? `${r.programme} (ex æquo)` : r.programme);
dash.draw('c_fourchette', (el) => {
  const d = dash.data('incertitude_tab');
  if (!cpPret(el, d)) return;
  el.replaceChildren();
  const p = cpInc(), u = INC_UNITE[p.grandeur], dec = INC_DEC[p.grandeur];
  const rows = incLignes().sort((a, b) => a.p50_rho1 - b.p50_rho1);
  if (!rows.length) return;
  const sq = rows.find((r) => r.dossier === 'statu_quo');
  const choisi = cpProgDetail();
  const W = Math.max(280, el.clientWidth), pas = 30, H = rows.length * pas + 28;
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
    .attr('aria-label', `Fourchette de chaque programme en ${p.annee}, du plus bas au plus haut`);
  const m = svg.append('g').style('font-size', 'var(--cds-font-size-caption)');
  let ml = 0;
  m.selectAll('text').data(rows).join('text').text(incNom).each(function () { ml = Math.max(ml, this.getComputedTextLength()); });
  m.remove();
  ml = Math.min(ml + 12, W * 0.42);
  const lab = (r) => `${cpFmt(r.p10_rho1, dec)} – ${cpFmt(r.p90_rho1, dec)}`;
  const essai = svg.append('text').style('font-size', 'var(--cds-font-size-caption)').text(lab(rows.reduce((a, b) => (lab(a).length > lab(b).length ? a : b))));
  const lw = essai.node().getComputedTextLength() + 10;
  essai.remove();
  const lo = d3.min(rows, (r) => Math.min(r.p10_rho0, r.p10_rho1)), hi = d3.max(rows, (r) => Math.max(r.p90_rho0, r.p90_rho1));
  const x = d3.scaleLinear([Math.min(0, lo), hi], [ml, W - lw]).nice();
  if (x.domain()[0] < 0) svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', 0).attr('y2', H - 20).style('stroke', 'var(--cds-chart-reference)');
  if (sq) svg.append('line').attr('x1', x(sq.p50_rho1)).attr('x2', x(sq.p50_rho1)).attr('y1', 0).attr('y2', H - 20).style('stroke', 'var(--cds-chart-muted)').attr('stroke-dasharray', '4 3');
  const g = svg.selectAll('g.ligne').data(rows).join('g').attr('class', 'ligne').attr('transform', (r, i) => `translate(0,${i * pas})`);
  g.append('rect').attr('x', 0).attr('y', 0).attr('width', W).attr('height', pas).attr('fill', 'transparent');
  g.append('text').attr('x', 0).attr('y', pas / 2).attr('dy', '0.35em').text(incNom)
    .style('fill', (r) => (r.dossier === 'statu_quo' ? 'var(--color-fg-muted)' : 'var(--color-fg)')).style('font-weight', (r) => (r.programme === choisi ? 600 : null)).style('font-size', 'var(--cds-font-size-caption)');
  const coul = (r) => (r.dossier === 'statu_quo' ? 'var(--cds-chart-muted)' : dash.colors[0]);
  g.append('rect').attr('x', (r) => x(r.p10_rho1)).attr('y', 7).attr('height', pas - 14).attr('rx', 3).attr('width', (r) => Math.max(1, x(r.p90_rho1) - x(r.p10_rho1))).style('fill', coul).style('opacity', 0.28);
  g.append('rect').attr('x', (r) => x(r.p10_rho0)).attr('y', pas / 2 - 3).attr('height', 6).attr('rx', 2).attr('width', (r) => Math.max(1, x(r.p90_rho0) - x(r.p10_rho0))).style('fill', coul);
  g.append('circle').attr('cx', (r) => x(r.p50_rho1)).attr('cy', pas / 2).attr('r', 4.5).style('fill', 'var(--color-bg)').style('stroke', coul).attr('stroke-width', 2);
  g.append('text').attr('x', W - lw + 6).attr('y', pas / 2).attr('dy', '0.35em').text(lab).style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)').style('font-variant-numeric', 'tabular-nums');
  const gx = svg.append('g').attr('transform', `translate(0,${H - 20})`).call(d3.axisBottom(x).ticks(Math.max(3, Math.floor(W / 110))).tickFormat((v) => cpFmt(v, 0)));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  const tip = d3.select(el).append('div').attr('class', 'tip').style('display', 'none');
  g.on('pointermove', (ev, r) => {
    tip.style('display', null).selectAll('*').remove();
    tip.append('div').attr('class', 't').text(`${r.programme}, ${p.annee}`);
    tip.append('div').text(`Médiane : ${cpFmt(r.p50_rho1, dec)}${u}`);
    if (r.ex_aequo) tip.append('div').text(`Ex æquo avec : ${r.ex_aequo}`);
    tip.append('div').text(`Indépendantes : ${cpFmt(r.p10_rho0, dec)} – ${cpFmt(r.p90_rho0, dec)}${u}`);
    tip.append('div').text(`Ensemble : ${cpFmt(r.p10_rho1, dec)} – ${cpFmt(r.p90_rho1, dec)}${u}`);
    if (p.grandeur === 'deficit' && r.proba_rho0 != null) tip.append('div').text(`Mieux que le statu quo : ${cpFmt(r.proba_rho0, 0)} à ${cpFmt(r.proba_rho1, 0)} % des tirages`);
    const [mx, my] = d3.pointer(ev, el);
    const bw = el.clientWidth, tw = tip.node().offsetWidth;
    tip.style('left', `${Math.max(0, Math.min(bw - tw, mx + 12))}px`).style('top', `${my + 14}px`);
  }).on('pointerleave', () => tip.style('display', 'none'));
});
dash.draw('t_incertitude', (tb) => {
  tb.replaceChildren();
  const rows = incLignes();
  if (!rows) return;
  const p = cpInc(), dec = INC_DEC[p.grandeur], u = INC_UNITE[p.grandeur];
  rows.sort((a, b) => (a.dossier === 'statu_quo' ? -1 : b.dossier === 'statu_quo' ? 1 : a.p50_rho1 - b.p50_rho1));
  for (const r of rows) {
    const pr = (v) => (p.grandeur !== 'deficit' || v == null ? '—' : cpFmt(v, 0) + ' %');
    const c = (v) => (p.grandeur === 'deficit' && r.dossier !== 'statu_quo' ? (v >= 90 ? 'bon' : (v <= 10 ? 'mauvais' : '')) : '');
    cpLigneTableau(tb, r.cle, [[incNom(r)], [cpFmt(r.p50_rho1, dec) + u], [`${cpFmt(r.p10_rho0, dec)} – ${cpFmt(r.p90_rho0, dec)}${u}`],
      [`${cpFmt(r.p10_rho1, dec)} – ${cpFmt(r.p90_rho1, dec)}${u}`], [pr(r.proba_rho0), c(r.proba_rho0)], [pr(r.proba_rho1), c(r.proba_rho1)], [r.hypotheses || '—']],
    (r.dossier === 'statu_quo' ? 'sq' : '') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});

// lectures des mesures floues qui pèsent le plus
dash.draw('t_lectures', (tb) => {
  const d = dash.data('lectures');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const rows = [...d.data].sort((a, b) => Math.abs(Number(b.poids_2037)) - Math.abs(Number(a.poids_2037)));
  for (const r of rows) {
    const v = Number(r.poids_2037);
    cpLigneTableau(tb, r.cle, [[r.programme], [r.lecture], [r.valeur], [cpSigne(v, 2), cpComparer(v, 0, 'haut')], [r.statut], [r.source]],
      r.programme === cpProgDetail() ? 'choisi' : '');
  }
});
