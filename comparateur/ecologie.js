// Écologie : émissions, empreinte, budgets carbone, secteurs, mesures
const eco = (el, prog, champ, d = 1, o = {}) => cpValeurCle(el, 'ecologie', prog, champ, { d, ...o });
const ligneEco = (prog) => {
  const e = dash.data('ecologie');
  return e.status === 'ok' ? e.data.find((x) => x.cle === `${prog}|${cpParams().scenario}|${cpParams().annee}`) : null;
};
// [tuile, champ, décimales, sens]
for (const [nom, champ, d, sens, seuil] of [['hab', 'territoriales_hab_t', 2, 'bas', 0.005], ['emp', 'empreinte_hab_t', 2, 'bas', 0.005],
  ['mt', 'territoriales_mt', 0, 'bas', 0.5], ['snbc', 'ecart_snbc_cumule_mt', 0, 'bas', 0.5]]) {
  dash.draw('e_' + nom + '_prog', (el) => { const v = eco(el, cpProgDetail(), champ, d); const r = ligneEco(CP_SQ); cpClasse(el, v, r ? Number(r[champ]) : null, sens, seuil); });
  dash.draw('e_' + nom + '_sq', (el) => eco(el, CP_SQ, champ, d));
}
dash.draw('e_hab_prog2', (el) => { const v = eco(el, cpProgDetail(), 'territoriales_hab_t', 2); const r = ligneEco(CP_SQ); cpClasse(el, v, r ? Number(r.territoriales_hab_t) : null, 'bas', 0.005); });
dash.draw('e_hab_sq2', (el) => eco(el, CP_SQ, 'territoriales_hab_t', 2));
dash.draw('e_mesures_prog', (el) => { const v = eco(el, cpProgDetail(), 'effet_mesures_mt', 1, { signe: true }); cpClasse(el, v, 0, 'bas', 0.05); });
dash.draw('e_activite_prog', (el) => eco(el, cpProgDetail(), 'effet_activite_mt', 1, { signe: true }));
dash.draw('t_climat', (tb) => {
  const e = dash.data('ecologie');
  tb.replaceChildren();
  if (e.status !== 'ok') return;
  const p = cpParams();
  const rows = e.data.filter((r) => r.scenario === p.scenario && Number(r.annee) === p.annee)
    .sort((a, b) => (a.programme === CP_SQ ? -1 : b.programme === CP_SQ ? 1 : Number(a.territoriales_mt) - Number(b.territoriales_mt)));
  const sq = rows.find((r) => r.programme === CP_SQ);
  for (const r of rows) {
    const estSq = r.programme === CP_SQ;
    const c = (k, ref, s) => (estSq || !sq ? '' : cpComparer(Number(r[k]), ref ?? Number(sq[k]), 'bas', s));
    cpLigneTableau(tb, r.cle, [[r.programme], [cpFmt(Number(r.territoriales_mt), 0), c('territoriales_mt', null, 0.5)],
      [cpFmt(Number(r.territoriales_hab_t), 2), c('territoriales_hab_t', null, 0.005)], [cpFmt(Number(r.empreinte_hab_t), 2), c('empreinte_hab_t', null, 0.005)],
      [cpSigne(Number(r.effet_mesures_mt), 1), c('effet_mesures_mt', 0, 0.05)], [cpSigne(Number(r.effet_activite_mt), 1)],
      [cpSigne(Number(r.ecart_snbc_cumule_mt), 0), c('ecart_snbc_cumule_mt', null, 0.5)]],
    (estSq ? 'sq' : '') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});
dash.draw('c_emissions', (el) => {
  const e = dash.data('ecologie');
  if (!cpPret(el, e)) return;
  const s = cpProgrammes().map((prog) => cpSerie(e, prog, 'territoriales_mt'));
  const plafond = cpSerie(e, CP_SQ, 'plafond_snbc_mt');
  s.push({ ...plafond, nom: 'Plafond des budgets carbone (SNBC)', prog: 'plafond', horsRang: true, couleur: 'var(--color-warn)', tirets: '1 4' });
  cpLignes(el, s, ' Mt', true, 'bas', 0);
});
dash.draw('c_empreinte', cpParProgramme('ecologie', 'empreinte_hab_t', ' t', true, 'bas', { dec: 2 }));
dash.draw('c_effet_mesures', (el) => {
  const e = dash.data('ecologie');
  if (!cpPret(el, e)) return;
  cpLignes(el, cpProgrammes().filter((x) => x !== CP_SQ).map((prog) => cpSerie(e, prog, 'effet_mesures_mt')), ' Mt', true, 'bas', 1);
});
dash.calc('eco_secteurs', {
  inputs: ['ecologie'],
  title: 'Émissions par secteur contre le statu quo',
  description: 'Émissions de chaque secteur du programme et du statu quo, et leur écart, en Mt CO2e, par scénario et par année.',
  fn: (ecologie) => {
    const secteurs = [['transports', 'Transports'], ['batiments', 'Bâtiments'], ['industrie', 'Industrie'], ['energie', 'Énergie'], ['agriculture', 'Agriculture'], ['dechets', 'Déchets et divers']];
    const sq = new Map();
    for (const r of ecologie) if (r.programme === 'Statu quo') sq.set(r.scenario + '|' + r.annee, r);
    const out = [];
    for (const r of ecologie) {
      const b = sq.get(r.scenario + '|' + r.annee);
      if (r.programme === 'Statu quo' || !b) continue;
      for (const [k, nom] of secteurs) {
        const v = Number(r['secteur_' + k + '_mt']), w = Number(b['secteur_' + k + '_mt']);
        out.push({ cle: `${r.programme}|${r.scenario}|${r.annee}|${nom}`, programme: r.programme, scenario: r.scenario, annee: r.annee, secteur: nom, programme_mt: v, statu_quo_mt: w, ecart_mt: v - w });
      }
    }
    return out;
  },
});
dash.draw('c_secteurs', (el) => {
  const d = dash.data('eco_secteurs');
  if (!cpPret(el, d)) return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee)
    .map((r) => ({ nom: r.secteur, v: Number(r.ecart_mt), lab: `${cpSigne(Number(r.ecart_mt), 1)} Mt (${cpFmt(Number(r.programme_mt), 0)} contre ${cpFmt(Number(r.statu_quo_mt), 0)})` }));
  cpBarres(el, rows, { bon: 'negatif', aria: `Émissions par secteur contre le statu quo, ${prog}, ${p.annee}` });
});
const SECTEURS_ECO = { transports: 'Transports', batiments: 'Bâtiments', industrie: 'Industrie', energie: 'Énergie', agriculture: 'Agriculture', dechets: 'Déchets', importations: 'Importations' };
dash.draw('t_eco_mesures', (tb) => {
  const d = dash.data('ecologie_mesures');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee && Math.abs(Number(r.mt)) >= 0.005)
    .sort((a, b) => Number(a.mt) - Number(b.mt));
  for (const r of rows) {
    const v = Number(r.mt);
    cpLigneTableau(tb, r.cle, [[r.mesure], [SECTEURS_ECO[r.secteur] || r.secteur], [cpSigne(v, 2), v < -0.005 ? 'bon' : (v > 0.005 ? 'mauvais' : '')]]);
  }
});
