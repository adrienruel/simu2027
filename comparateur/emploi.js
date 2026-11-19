// Emploi : chômage, emploi, taux d'emploi, emploi mesure par mesure
dash.calc('emploi_tab', {
  inputs: ['traj'],
  title: 'Emploi par programme',
  description: "Chômage, personnes en emploi, écart au statu quo et taux d'emploi et d'activité des 18-66 ans, par programme, scénario et année.",
  fn: (traj) => traj.map((r) => ({
    cle: r.programme + '|' + r.scenario + '|' + r.annee, programme: r.programme, scenario: r.scenario, annee: r.annee,
    chomage: Number(r.chomage), emploi_millions: Number(r.emploi_millions), ecart_emploi_milliers: Number(r.ecart_emploi_milliers),
    taux_emploi_18_66: Number(r.taux_emploi_18_66), taux_activite_18_66: Number(r.taux_activite_18_66),
  })),
});
dash.draw('m_chom_prog', (el) => { const v = cpValeur(el, 'traj', cpProgDetail(), 'chomage'); const r = cpLigneTraj(CP_SQ); cpClasse(el, v, r ? Number(r.chomage) : null, 'bas'); });
dash.draw('m_chom_sq', (el) => cpValeur(el, 'traj', CP_SQ, 'chomage'));
dash.draw('m_ecart_prog', (el) => { const v = cpValeur(el, 'traj', cpProgDetail(), 'ecart_emploi_milliers', { d: 0, signe: true }); cpClasse(el, v, 0, 'haut', 5); });
dash.draw('m_ecart_total', (el) => cpValeur(el, 'traj', cpProgDetail(), 'ecart_emploi_milliers', { d: 0, signe: true }));
dash.draw('t_emploi', (tb) => {
  const d = dash.data('emploi_tab');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams();
  const rows = d.data.filter((r) => r.scenario === p.scenario && Number(r.annee) === p.annee)
    .sort((a, b) => (a.programme === CP_SQ ? -1 : b.programme === CP_SQ ? 1 : a.chomage - b.chomage));
  const sq = rows.find((r) => r.programme === CP_SQ);
  for (const r of rows) {
    const estSq = r.programme === CP_SQ;
    const c = (k, sens, s) => (estSq || !sq ? '' : cpComparer(r[k], k === 'ecart_emploi_milliers' ? 0 : sq[k], sens, s));
    cpLigneTableau(tb, r.cle, [[r.programme], [cpFmt(r.chomage, 1), c('chomage', 'bas')], [cpFmt(r.emploi_millions, 2)],
      [cpSigne(r.ecart_emploi_milliers, 0), c('ecart_emploi_milliers', 'haut', 5)], [cpFmt(r.taux_emploi_18_66, 1), c('taux_emploi_18_66', 'haut')],
      [cpFmt(r.taux_activite_18_66, 1), c('taux_activite_18_66', 'haut')]], (estSq ? 'sq' : '') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});
dash.draw('c_chomage', cpParProgramme('traj', 'chomage', ' %', true, 'bas'));
dash.draw('c_taux_emploi', cpParProgramme('traj', 'taux_emploi_18_66', ' %', false, 'haut'));
dash.draw('c_ecart_emploi', (el) => {
  const d = dash.data('traj');
  if (!cpPret(el, d)) return;
  cpLignes(el, cpProgrammes().filter((x) => x !== CP_SQ).map((prog) => cpSerie(d, prog, 'ecart_emploi_milliers')), ' milliers', true, 'haut', 0);
});
dash.draw('c_canaux', (el) => {
  const d = dash.data('emploi_canaux');
  if (!cpPret(el, d)) return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee && Math.abs(Number(r.emplois_milliers)) >= 0.5)
    .map((r) => ({ nom: r.canal, v: Number(r.emplois_milliers), lab: `${cpSigne(Number(r.emplois_milliers), 0)} milliers` })).sort((a, b) => b.v - a.v);
  cpBarres(el, rows, { dec: 0, aria: `Emplois en plus ou en moins par mesure, ${prog}, ${p.annee}` });
});
dash.draw('t_canaux', (tb) => {
  const d = dash.data('emploi_canaux');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee && Math.abs(Number(r.emplois_milliers)) >= 0.05)
    .sort((a, b) => Math.abs(Number(b.emplois_milliers)) - Math.abs(Number(a.emplois_milliers)));
  for (const r of rows) {
    const v = Number(r.emplois_milliers);
    cpLigneTableau(tb, r.cle, [[r.canal], [cpSigne(v, 1), v > 0.05 ? 'bon' : (v < -0.05 ? 'mauvais' : '')]]);
  }
});
