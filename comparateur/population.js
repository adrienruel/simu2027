// Population : démographie (naissances, décès, migrations, fécondité, âges), pauvreté, déciles
window.cpAnneeDemo = () => Math.min(2072, Math.max(2030, cpParams().annee));
const demo = (el, prog, champ, o = {}) => cpValeurCle(el, 'demographie', prog, champ, { annee: cpAnneeDemo(), ...o });
const ligneDemo = (prog) => {
  const d = dash.data('demographie');
  return d.status === 'ok' ? d.data.find((x) => x.cle === `${prog}|${cpParams().scenario}|${cpAnneeDemo()}`) : null;
};
dash.draw('pop_annee', (el) => { el.textContent = String(cpAnneeDemo()); });
// [tuile, champ, décimales, sens (null : pas de jugement)]
const TUILES_DEMO = [['pop', 'population_millions', 2, null], ['nais', 'naissances_milliers', 0, null], ['dec', 'deces_milliers', 0, null],
  ['nat', 'solde_naturel_milliers', 0, null], ['mig', 'solde_migratoire_milliers', 0, null], ['icf', 'fecondite', 2, null],
  ['p65', 'part_65_plus_pct', 1, null], ['dep', 'dependance_65_20_64', 1, 'bas'], ['age', 'age_median', 1, null]];
for (const [nom, champ, d, sens] of TUILES_DEMO) {
  dash.draw('d_' + nom, (el) => {
    const v = demo(el, cpProgDetail(), champ, { d });
    const r = ligneDemo(CP_SQ);
    if (sens) cpClasse(el, v, r ? Number(r[champ]) : null, sens);
  });
  dash.draw('d_' + nom + '_sq', (el) => demo(el, CP_SQ, champ, { d }));
}
dash.draw('l_pop_prog', (el) => demo(el, cpProgDetail(), 'population_millions', { d: 1 }));
dash.draw('l_pop_sq', (el) => demo(el, CP_SQ, 'population_millions', { d: 1 }));
dash.draw('l_pop_ecart', (el) => demo(el, cpProgDetail(), 'ecart_population_milliers', { d: 0, signe: true }));

const demoLignes = (col, unite, zero, sens, dec, sansSq) => (el) => {
  const d = dash.data('demographie');
  if (!cpPret(el, d)) return;
  const progs = cpProgrammes().filter((x) => !sansSq || x !== CP_SQ);
  cpLignes(el, progs.map((prog) => cpSerie(d, prog, col)), unite, zero, sens, dec);
};
dash.draw('c_population', demoLignes('population_millions', ' M', false, null, 2));
dash.draw('c_migration', demoLignes('solde_migratoire_milliers', ' milliers', true, null, 0));
dash.draw('c_naissances', demoLignes('naissances_milliers', ' milliers', false, null, 0));
dash.draw('c_deces', demoLignes('deces_milliers', ' milliers', false, null, 0));
dash.draw('c_fecondite', demoLignes('fecondite', '', false, null, 2));
dash.draw('c_dependance', demoLignes('dependance_65_20_64', '', false, 'bas', 1));

// pyramide des âges : programme contre statu quo
window.cpAnneePyr = () => cpProche([2029, 2037, 2050, 2060]);
dash.draw('pyr_annee', (el) => { el.textContent = String(cpAnneePyr()); });
dash.draw('c_pyramide', (el) => {
  const d = dash.data('pyramide');
  if (!cpPret(el, d)) return;
  el.replaceChildren();
  const p = cpParams(), prog = cpProgDetail(), an = cpAnneePyr();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === an)
    .map((r) => ({ t: r.tranche, a: Number(r.age_debut), v: Number(r.milliers), s: Number(r.statu_quo_milliers) }))
    .sort((x, y) => y.a - x.a);
  if (!rows.length) return;
  const W = Math.max(280, el.clientWidth), pas = 17, H = rows.length * pas + 26, ml = 46;
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
    .attr('aria-label', `Population par tranche d'âge en ${an}, ${prog} contre le statu quo`);
  const lab = (r) => `${cpSigne(r.v - r.s, 0)} milliers`;
  const essai = svg.append('text').style('font-size', 'var(--cds-font-size-caption)').text(lab(rows.reduce((a, b) => (lab(a).length > lab(b).length ? a : b))));
  const lw = essai.node().getComputedTextLength() + 12;
  essai.remove();
  const x = d3.scaleLinear([0, d3.max(rows, (r) => Math.max(r.v, r.s))], [ml, W - lw]).nice();
  const g = svg.selectAll('g.age').data(rows).join('g').attr('class', 'age').attr('transform', (r, i) => `translate(0,${i * pas})`);
  g.append('text').attr('x', ml - 6).attr('y', pas / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => r.t)
    .style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  g.append('rect').attr('x', ml).attr('y', 2).attr('height', pas - 4).attr('width', (r) => Math.max(0, x(r.v) - ml)).attr('rx', 2).style('fill', dash.colors[0]);
  g.append('line').attr('x1', (r) => x(r.s)).attr('x2', (r) => x(r.s)).attr('y1', 0).attr('y2', pas).style('stroke', 'var(--color-fg)').attr('stroke-width', 2);
  g.append('text').attr('x', W - lw + 6).attr('y', pas / 2).attr('dy', '0.35em').text(lab)
    .style('fill', (r) => (Math.abs(r.v - r.s) < 0.5 ? 'var(--cds-text-secondary)' : 'var(--color-fg)')).style('font-size', 'var(--cds-font-size-caption)').style('font-variant-numeric', 'tabular-nums');
  const gx = svg.append('g').attr('transform', `translate(0,${H - 22})`).call(d3.axisBottom(x).ticks(Math.max(3, Math.floor(W / 120))).tickFormat((v) => cpFmt(v, 0)));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  const tip = d3.select(el).append('div').attr('class', 'tip').style('display', 'none');
  g.append('rect').attr('x', 0).attr('y', 0).attr('width', W).attr('height', pas).attr('fill', 'transparent')
    .on('pointermove', (ev, r) => {
      tip.style('display', null).selectAll('*').remove();
      tip.append('div').attr('class', 't').text(`${r.t} ans, ${an}`);
      tip.append('div').text(`${prog} : ${cpFmt(r.v, 0)} milliers`);
      tip.append('div').text(`Statu quo : ${cpFmt(r.s, 0)} milliers`);
      const [mx, my] = d3.pointer(ev, el);
      const bw = el.clientWidth, tw = tip.node().offsetWidth;
      tip.style('left', `${Math.max(0, Math.min(bw - tw, mx + 12))}px`).style('top', `${my + 14}px`);
    }).on('pointerleave', () => tip.style('display', 'none'));
});

// pauvreté au fil des années (microsimulation, scénario prudent seulement)
window.cpAnneeMicro = () => cpProche([2029, 2032, 2037, 2050]);
dash.draw('p_annee', (el) => { el.textContent = String(cpAnneeMicro()); });
dash.draw('p_prog', (el) => { const prog = cpProgDetail(); cpValeurCle(el, 'redistribution', prog, 'pauvrete_pct', { cle: `${prog}|${cpAnneeMicro()}`, absent: 'non calculé' }); });
dash.draw('p_sq', (el) => { const prog = cpProgDetail(); cpValeurCle(el, 'redistribution', prog, 'pauvrete_pct_sq', { cle: `${prog}|${cpAnneeMicro()}` }); });
dash.draw('c_pauvrete', (el) => {
  const d = dash.data('redistribution');
  if (!cpPret(el, d)) return;
  const s = cpProgrammes().map((prog) => ({
    nom: prog, prog, couleur: cpCouleur(prog), tirets: prog === CP_SQ, marques: true,
    points: d.data.filter((r) => r.programme === prog).map((r) => [Number(r.annee), Number(r.pauvrete_pct)]).sort((a, b) => a[0] - b[0]),
  })).filter((x) => x.points.length);
  cpLignes(el, s, ' %', false, 'bas', 1);
});
dash.draw('t_redis', (tb) => {
  const d = dash.data('redistribution');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const an = cpAnneeMicro();
  const rows = d.data.filter((r) => Number(r.annee) === an)
    .sort((a, b) => (a.programme === CP_SQ ? -1 : b.programme === CP_SQ ? 1 : Number(a.pauvrete_pct) - Number(b.pauvrete_pct)));
  const sq = rows.find((r) => r.programme === CP_SQ);
  for (const r of rows) {
    const estSq = r.programme === CP_SQ;
    const c = (k, s) => (estSq || !sq ? '' : cpComparer(Number(r[k]), Number(sq[k]), 'bas', s));
    cpLigneTableau(tb, r.cle, [[r.programme], [cpFmt(Number(r.pauvrete_pct), 1), c('pauvrete_pct', 0.1)], [estSq ? '—' : cpFmt(Number(r.pauvrete_pct_sq), 1)],
      [cpFmt(Number(r.gini), 3), c('gini', 0.0015)], [cpFmt(Number(r.d9_d1), 2), c('d9_d1', 0.01)], [cpFmt(Number(r.mediane), 0)],
      [estSq ? '—' : cpFmt(Number(r.couverture_menages_pct), 0) + ' %'], [estSq ? '—' : (r.mesures_codees || '—')]],
    (estSq ? 'sq' : '') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});

// déciles au fil des années : publiés seulement si la micro couvre au moins 80 % du budget « ménages »
const ANNEES_MICRO = [2029, 2032, 2037, 2050];
dash.onData(() => { ANNEES_MICRO.forEach((a, i) => { for (const s of document.querySelectorAll(`.cp .leg-dec [data-an="${a}"]`)) s.style.setProperty('--sw', dash.colors[i % dash.colors.length]); }); });
dash.draw('c_deciles_evol', (el) => {
  const d = dash.data('redistribution_deciles');
  if (!cpPret(el, d)) return;
  el.replaceChildren();
  const prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog).map((r) => ({ dec: Number(r.decile), an: Number(r.annee), v: Number(r.variation_pct), eur: Number(r.variation_eur_an), g: Number(r.gagnants_pct), pe: Number(r.perdants_pct) }));
  if (!rows.length) return;
  const W = Math.max(280, el.clientWidth), H = 280, B = 24;
  const ext = d3.extent(rows, (r) => r.v);
  const y = d3.scaleLinear([Math.min(0, ext[0]), Math.max(0, ext[1])], [H - B, 12]).nice();
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
    .attr('aria-label', `Variation du niveau de vie par décile et par année, ${prog}`);
  const gy = svg.append('g').call(d3.axisLeft(y).ticks(5).tickFormat((v) => cpFmt(v, 1)));
  gy.attr('font-size', null).attr('font-family', null);
  let ml = 0; gy.selectAll('text').each(function () { ml = Math.max(ml, this.getComputedTextLength()); });
  ml += 10;
  gy.attr('transform', `translate(${ml},0)`);
  gy.select('.domain').remove();
  gy.selectAll('line').attr('x2', W - ml - 8).style('stroke', 'var(--cds-chart-grid)');
  gy.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
  const x0 = d3.scaleBand(d3.range(1, 11), [ml, W - 8]).paddingInner(0.2);
  const ans = ANNEES_MICRO.filter((a) => rows.some((r) => r.an === a));
  const x1 = d3.scaleBand(ans, [0, x0.bandwidth()]).padding(0.08);
  svg.append('line').attr('x1', ml).attr('x2', W - 8).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-reference)');
  svg.append('g').selectAll('rect').data(rows).join('rect')
    .attr('x', (r) => x0(r.dec) + x1(r.an)).attr('width', x1.bandwidth())
    .attr('y', (r) => Math.min(y(0), y(r.v))).attr('height', (r) => Math.max(1, Math.abs(y(r.v) - y(0)))).attr('rx', 1.5)
    .style('fill', (r) => dash.colors[ANNEES_MICRO.indexOf(r.an) % dash.colors.length]);
  const gx = svg.append('g').attr('transform', `translate(0,${H - B})`).call(d3.axisBottom(x0).tickFormat((v) => `D${v}`).tickSize(0));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').remove();
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)').attr('dy', '1em');
  const tip = d3.select(el).append('div').attr('class', 'tip').style('display', 'none');
  svg.append('g').selectAll('rect').data(d3.range(1, 11)).join('rect').attr('x', (k) => x0(k)).attr('width', x0.bandwidth()).attr('y', 0).attr('height', H - B).attr('fill', 'transparent')
    .on('pointermove', (ev, k) => {
      tip.style('display', null).selectAll('*').remove();
      tip.append('div').attr('class', 't').text(`Décile ${k}`);
      for (const r of rows.filter((q) => q.dec === k).sort((a, b) => a.an - b.an)) {
        tip.append('div').text(`${r.an} : ${cpSigne(r.v, 1)} % (${cpSigne(r.eur, 0)} €/an ; ${cpFmt(r.g, 0)} % gagnants, ${cpFmt(r.pe, 0)} % perdants)`);
      }
      const [mx, my] = d3.pointer(ev, el);
      const bw = el.clientWidth, tw = tip.node().offsetWidth;
      tip.style('left', `${Math.max(0, Math.min(bw - tw, mx + 12))}px`).style('top', `${my + 14}px`);
    }).on('pointerleave', () => tip.style('display', 'none'));
});
// déciles non publiés : part du budget « ménages » codée dans la micro
dash.calc('couverture_tab', {
  inputs: ['couverture_micro', 'incertitude'],
  title: 'Couverture de la microsimulation',
  description: "Part du budget « ménages » de chaque programme codée dans la microsimulation en 2032, mesures les plus lourdes non codées, et décision de publier les déciles (au moins 80 %). Le nom du programme vient de la table d'incertitude, qui donne aussi son dossier.",
  fn: (couverture_micro, incertitude) => {
    const noms = new Map(incertitude.map((r) => [r.dossier, r.programme]));
    return couverture_micro.map((r) => ({ cle: noms.get(r.programme) || r.programme, programme: noms.get(r.programme) || r.programme, part_codee_pct: Number(r.part_codee_pct), deciles_publies: r.deciles_publies === '1', plus_lourdes_non_codees: r.plus_lourdes_non_codees }));
  },
});
dash.onData(() => {
  const d = dash.data('redistribution_deciles');
  const prog = cpProgDetail();
  const ok = d.status === 'ok';
  const a = ok && d.data.some((r) => r.programme === prog);
  for (const el of document.querySelectorAll('.cp .dec-presents')) el.hidden = ok && !a;
  for (const el of document.querySelectorAll('.cp .dec-absents')) el.hidden = !ok || a;
});
dash.draw('cv_part', (el) => cpValeurCle(el, 'couverture_tab', cpProgDetail(), 'part_codee_pct', { cle: cpProgDetail(), d: 0 }));
dash.draw('cv_lourdes', (el) => {
  const d = dash.data('couverture_tab');
  const prog = cpProgDetail();
  const r = d.status === 'ok' ? d.data.find((x) => x.cle === prog) : null;
  el.dataset.where = `cle=${encodeURIComponent(prog || '')}`;
  el.textContent = r && r.plus_lourdes_non_codees ? r.plus_lourdes_non_codees : '—';
});
