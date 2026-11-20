// Comparer deux programmes : indicateurs côte à côte, courbes superposées, écart par poste
window.cpProgB = () => {
  const progs = cpProgrammes().filter((x) => x !== CP_SQ && x !== cpProgDetail());
  const b = dash.params().programme_b;
  return progs.includes(b) ? b : (progs[0] || null);
};
dash.draw('f_prog_b', (sel) => {
  const progs = cpProgrammes().filter((x) => x !== CP_SQ && x !== cpProgDetail());
  sel.replaceChildren(...progs.map((x) => new Option(x, x)));
  sel.value = cpProgB() || '';
  sel.onchange = () => dash.setParams({ programme_b: sel.value || null });
});
dash.draw('l_prog_b', (el) => { el.textContent = cpProgB() || '—'; });
dash.draw('l_prog_a', (el) => { el.textContent = cpProgDetail() || '—'; });
for (const b of document.querySelectorAll('.cp .f-inverser')) b.addEventListener('click', () => {
  const a = cpProgDetail(), bb = cpProgB();
  if (a && bb) dash.setParams({ programme: bb, programme_b: a });
});

// indicateurs : [clé, libellé, source, champ, décimales, sens (plus bas ou plus haut = mieux), unité, type de clé]
dash.calc('comparaison', {
  inputs: ['traj', 'croissance', 'demographie', 'redistribution', 'ecologie'],
  title: 'Deux programmes côte à côte',
  description: "Indicateurs clés des deux programmes choisis et du statu quo, au scénario et à l'année choisis (démographie : 2030 au plus tôt ; pauvreté : année calculée la plus proche, scénario prudent). Colonne « écart » : programme B moins programme A.",
  fn: (traj, croissance, demographie, redistribution, ecologie) => {
    const prm = dash.params();
    const scen = prm.scenario || 'Prudent', an = Number(prm.annee || 2037);
    const progs = [...new Set(traj.map((r) => r.programme))].filter((x) => x !== 'Statu quo');
    const a = progs.includes(prm.programme) ? prm.programme : progs[0];
    const autres = progs.filter((x) => x !== a);
    const b = autres.includes(prm.programme_b) ? prm.programme_b : autres[0];
    const src = { traj, croissance, demographie, redistribution, ecologie };
    const anDemo = Math.min(2072, Math.max(2030, an));
    const anMicro = [2029, 2032, 2037, 2050].reduce((x, y) => (Math.abs(y - an) < Math.abs(x - an) ? y : x));
    const val = (s, champ, type, prog) => {
      const rows = src[s];
      let r;
      if (type === 'traj') r = rows.find((x) => x.programme === prog && x.scenario === scen && Number(x.annee) === an);
      else if (type === 'demo') r = rows.find((x) => x.cle === `${prog}|${scen}|${anDemo}`);
      else if (type === 'micro') r = rows.find((x) => x.cle === `${prog}|${anMicro}`);
      else r = rows.find((x) => x.cle === `${prog}|${scen}|${an}`);
      return r && r[champ] !== '' && r[champ] != null ? Number(r[champ]) : null;
    };
    return [
      ['esp', "Écart de solde primaire au statu quo (points de PIB)", 'traj', 'ecart_solde_primaire_pib', 2, 'haut', '', 'traj'],
      ['deficit', 'Déficit public (% du PIB)', 'traj', 'deficit', 1, 'bas', ' %', 'traj'],
      ['dette', 'Dette publique (% du PIB)', 'traj', 'dette_pib', 0, 'bas', ' %', 'traj'],
      ['recettes', 'Recettes publiques (% du PIB)', 'traj', 'recettes_pib', 1, null, ' %', 'traj'],
      ['depenses', 'Dépenses hors intérêts (% du PIB)', 'traj', 'depenses_primaires_pib', 1, null, ' %', 'traj'],
      ['pib', 'PIB, écart au statu quo (%)', 'croissance', 'ecart_pib_pct', 1, 'haut', ' %', 'cle'],
      ['croissance', "Croissance du PIB dans l'année (%)", 'croissance', 'croissance_pct', 2, 'haut', ' %', 'cle'],
      ['chomage', 'Chômage (%)', 'traj', 'chomage', 1, 'bas', ' %', 'traj'],
      ['emploi', 'Emploi, écart au statu quo (milliers)', 'traj', 'ecart_emploi_milliers', 0, 'haut', '', 'traj'],
      ['taux_emploi', "Taux d'emploi des 18-66 ans (%)", 'traj', 'taux_emploi_18_66', 1, 'haut', ' %', 'traj'],
      ['population', 'Population (millions)', 'traj', 'population_millions', 2, null, '', 'traj'],
      ['migration', 'Solde migratoire (milliers par an)', 'demographie', 'solde_migratoire_milliers', 0, null, '', 'demo'],
      ['fecondite', 'Fécondité (enfants par femme)', 'demographie', 'fecondite', 2, null, '', 'demo'],
      ['dependance', '65 ans ou plus pour 100 personnes de 20 à 64 ans', 'demographie', 'dependance_65_20_64', 1, 'bas', '', 'demo'],
      ['pauvrete', 'Pauvreté (%), microsimulation, scénario prudent', 'redistribution', 'pauvrete_pct', 1, 'bas', ' %', 'micro'],
      ['emissions', 'Émissions par habitant (t CO₂e)', 'ecologie', 'territoriales_hab_t', 2, 'bas', '', 'cle'],
      ['empreinte', 'Empreinte par habitant (t CO₂e)', 'ecologie', 'empreinte_hab_t', 2, 'bas', '', 'cle'],
      ['snbc', 'Dépassement cumulé des budgets carbone (Mt)', 'ecologie', 'ecart_snbc_cumule_mt', 0, 'bas', '', 'cle'],
    ].map(([cle, indicateur, s, champ, dec, sens, unite, type]) => {
      const va = val(s, champ, type, a), vb = val(s, champ, type, b), vs = val(s, champ, type, 'Statu quo');
      return { cle, indicateur, programme_a: a, programme_b: b, a: va, b: vb, statu_quo: vs, ecart: va == null || vb == null ? null : vb - va, dec, sens, unite };
    });
  },
});
dash.draw('t_comparer', (tb) => {
  const d = dash.data('comparaison');
  tb.replaceChildren();
  if (d.status !== 'ok' || !Array.isArray(d.data)) return;
  for (const r of d.data) {
    const f = (v) => (v == null ? '—' : (r.cle === 'esp' || r.cle === 'emploi' ? cpSigne(v, r.dec) : cpFmt(v, r.dec)) + r.unite);
    const ca = r.sens && r.cle !== 'esp' && r.cle !== 'emploi' ? cpComparer(r.a, r.statu_quo, r.sens) : (r.sens ? cpComparer(r.a, 0, r.sens) : '');
    const cb = r.sens && r.cle !== 'esp' && r.cle !== 'emploi' ? cpComparer(r.b, r.statu_quo, r.sens) : (r.sens ? cpComparer(r.b, 0, r.sens) : '');
    const ce = r.sens ? cpComparer(r.ecart, 0, r.sens) : '';
    cpLigneTableau(tb, r.cle, [[r.indicateur], [f(r.a), ca], [f(r.b), cb], [r.ecart == null ? '—' : cpSigne(r.ecart, r.dec) + (r.unite === ' %' ? ' pt' : r.unite), ce], [f(r.statu_quo)]]);
  }
});

// courbes superposées : A, B et statu quo
const deuxSeries = (source, col, unite, zero, sens, dec, o = {}) => (el) => {
  const d = dash.data(source);
  if (!cpPret(el, d)) return;
  const a = cpProgDetail(), b = cpProgB();
  const s = [a, b, ...(o.sansSq ? [] : [CP_SQ])].filter(Boolean).map((prog, i) => ({ ...cpSerie(d, prog, col, o), couleur: prog === CP_SQ ? 'var(--cds-chart-muted)' : dash.colors[i] }));
  cpLignes(el, s, unite, zero, sens, dec);
};
dash.draw('c_cmp_esp', deuxSeries('traj', 'ecart_solde_primaire_pib', ' pt', true, 'haut', 2, { sansSq: true }));
dash.draw('c_cmp_deficit', deuxSeries('traj', 'deficit', ' %', true, 'bas', 1));
dash.draw('c_cmp_chomage', deuxSeries('traj', 'chomage', ' %', true, 'bas', 1));
dash.draw('c_cmp_pib', deuxSeries('croissance', 'ecart_pib_pct', ' %', true, 'haut', 1, { sansSq: true }));
dash.draw('c_cmp_emissions', deuxSeries('ecologie', 'territoriales_mt', ' Mt', true, 'bas', 0));
dash.draw('c_cmp_population', deuxSeries('demographie', 'population_millions', ' M', false, null, 2));

// écart par poste, les deux programmes l'un sous l'autre
dash.draw('c_cmp_postes', (el) => {
  const d = dash.data('ecarts');
  if (!cpPret(el, d)) return;
  el.replaceChildren();
  const p = cpParams(), a = cpProgDetail(), b = cpProgB();
  const de = (prog) => new Map(d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee).map((r) => [r.groupe, Number(r.part_pib)]));
  const ma = de(a), mb = de(b);
  const groupes = [...new Set([...ma.keys(), ...mb.keys()])]
    .sort((x, y) => Math.max(Math.abs(mb.get(y) || 0), Math.abs(ma.get(y) || 0)) - Math.max(Math.abs(mb.get(x) || 0), Math.abs(ma.get(x) || 0)));
  if (!groupes.length) return;
  const W = Math.max(280, el.clientWidth), pas = 34, H = groupes.length * pas + 28;
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img')
    .attr('aria-label', `Écart au statu quo par poste, ${a} et ${b}, ${p.annee}`);
  const mes = svg.append('g').style('font-size', 'var(--cds-font-size-caption)');
  let ml = 0;
  mes.selectAll('text').data(groupes).join('text').text((g) => g).each(function () { ml = Math.max(ml, this.getComputedTextLength()); });
  mes.remove();
  ml = Math.min(ml + 12, W * 0.42);
  const lw = 52;
  const m = d3.max(groupes, (g) => Math.max(Math.abs(ma.get(g) || 0), Math.abs(mb.get(g) || 0))) || 1;
  const x = d3.scaleLinear([-m, m], [ml + lw, W - lw]);
  svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', 0).attr('y2', H - 20).style('stroke', 'var(--cds-chart-reference)');
  const g = svg.selectAll('g.ligne').data(groupes).join('g').attr('transform', (q, i) => `translate(0,${i * pas})`);
  g.append('text').attr('x', 0).attr('y', pas / 2).attr('dy', '0.35em').text((q) => q).style('fill', 'var(--color-fg)').style('font-size', 'var(--cds-font-size-caption)');
  for (const [k, mm, y0] of [[0, ma, 4], [1, mb, pas / 2]]) {
    g.append('rect').attr('x', (q) => Math.min(x(0), x(mm.get(q) || 0))).attr('y', y0).attr('height', pas / 2 - 5).attr('rx', 2)
      .attr('width', (q) => Math.max(1, Math.abs(x(mm.get(q) || 0) - x(0)))).style('fill', dash.colors[k]);
    g.append('text').attr('x', (q) => ((mm.get(q) || 0) >= 0 ? x(mm.get(q) || 0) + 4 : x(mm.get(q) || 0) - 4)).attr('y', y0 + (pas / 2 - 5) / 2).attr('dy', '0.35em')
      .attr('text-anchor', (q) => ((mm.get(q) || 0) >= 0 ? 'start' : 'end')).text((q) => cpSigne(mm.get(q) || 0, 2))
      .style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)').style('font-variant-numeric', 'tabular-nums');
  }
  const gx = svg.append('g').attr('transform', `translate(0,${H - 20})`).call(d3.axisBottom(x).ticks(5).tickFormat((v) => cpFmt(v, 1)));
  gx.attr('font-size', null).attr('font-family', null);
  gx.select('.domain').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
  gx.selectAll('text').style('fill', 'var(--cds-text-secondary)').style('font-size', 'var(--cds-font-size-caption)');
});
dash.onData(() => {
  for (const s of document.querySelectorAll('.cp .leg-ab .a')) s.style.setProperty('--sw', dash.colors[0]);
  for (const s of document.querySelectorAll('.cp .leg-ab .b')) s.style.setProperty('--sw', dash.colors[1]);
});
