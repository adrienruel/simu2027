// Économie : synthèse, croissance, déficit, dette, solde primaire, décomposition du déficit
dash.calc('synthese', {
  inputs: ['traj'],
  title: 'Synthèse par programme',
  description: 'Écart de solde primaire au statu quo, déficit, solde primaire et dette de chaque programme à quelques dates, première année où la dette dépasse 200 % du PIB, et années hors plausibilité.',
  fn: (traj) => {
    const par = new Map();
    for (const r of traj) {
      const cle = r.programme + '|' + r.scenario;
      const x = par.get(cle) || { cle, programme: r.programme, scenario: r.scenario, annee_200: null };
      const an = Number(r.annee);
      if (an === 2029) { x.deficit_2029 = Number(r.deficit); x.hors_2029 = r.hors_plausibilite === '1'; }
      if (an === 2032) x.esp_2032 = Number(r.ecart_solde_primaire_pib);
      if (an === 2037) { x.esp_2037 = Number(r.ecart_solde_primaire_pib); x.deficit_2037 = Number(r.deficit); x.sp_2037 = Number(r.solde_primaire_pib); x.dette_2037 = Number(r.dette_pib); x.pib_eq_2037 = Number(r.pib_pour_equilibrer_pct); x.hors_2037 = r.hors_plausibilite === '1'; }
      if (an === 2050) { x.deficit_2050 = Number(r.deficit); x.dette_2050 = Number(r.dette_pib); x.hors_2050 = r.hors_plausibilite === '1'; }
      if (Number(r.dette_pib) > 200 && (x.annee_200 === null || an < x.annee_200)) x.annee_200 = an;
      par.set(cle, x);
    }
    return [...par.values()];
  },
});
dash.draw('t_synthese', (tb) => {
  const d = dash.data('synthese');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams();
  const rows = d.data.filter((r) => r.scenario === p.scenario);
  const sq = rows.find((r) => r.programme === CP_SQ);
  rows.sort((a, b) => (a.programme === CP_SQ ? -1 : b.programme === CP_SQ ? 1 : b.esp_2037 - a.esp_2037));
  for (const r of rows) {
    const estSq = r.programme === CP_SQ;
    const c = (k, sens, hors) => (hors ? 'hors' : (estSq || !sq ? '' : cpComparer(r[k], sq[k], sens)));
    const ecart = (k) => [estSq ? '—' : cpSigne(r[k], 2), estSq ? '' : cpComparer(r[k], 0, 'haut')];
    cpLigneTableau(tb, r.cle, [
      [r.programme], ecart('esp_2032'), ecart('esp_2037'),
      [cpFmt(r.deficit_2029) + ' %', c('deficit_2029', 'bas', r.hors_2029)], [cpFmt(r.deficit_2037) + ' %', c('deficit_2037', 'bas', r.hors_2037)],
      [cpFmt(r.deficit_2050) + ' %', c('deficit_2050', 'bas', r.hors_2050)], [cpSigne(r.sp_2037) + ' %', c('sp_2037', 'haut', r.hors_2037)],
      [cpFmt(r.dette_2037, 0) + ' %', c('dette_2037', 'bas', r.hors_2037)], [cpFmt(r.dette_2050, 0) + ' %', c('dette_2050', 'bas', r.hors_2050)],
      [r.annee_200 == null ? 'jamais' : String(r.annee_200)],
      [estSq ? '—' : (r.pib_eq_2037 <= 0 ? 'aucun' : cpSigne(r.pib_eq_2037) + ' %')],
    ], (estSq ? 'sq' : '') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});

// croissance
dash.draw('e_pib_prog', (el) => cpValeurCle(el, 'croissance', cpProgDetail(), 'ecart_pib_pct', { signe: true, suffixe: ' %' }));
dash.draw('e_crois_prog', (el) => cpValeurCle(el, 'croissance', cpProgDetail(), 'croissance_pct', { d: 2, suffixe: ' %', absent: 'non calculée' }));
dash.draw('e_crois_sq', (el) => cpValeurCle(el, 'croissance', CP_SQ, 'croissance_pct', { d: 2, suffixe: ' %', absent: 'non calculée' }));
dash.draw('c_ecart_pib', (el) => {
  const d = dash.data('croissance');
  if (!cpPret(el, d)) return;
  const s = cpProgrammes().filter((x) => x !== CP_SQ).map((prog) => cpSerie(d, prog, 'ecart_pib_pct'));
  cpLignes(el, s, ' %', true, 'haut');
});
dash.draw('c_croissance', (el) => {
  const d = dash.data('croissance');
  if (!cpPret(el, d)) return;
  cpLignes(el, cpProgrammes().map((prog) => cpSerie(d, prog, 'croissance_pct', { debut: 2030 })), ' %', true, 'haut', 2);
});

// finances publiques
dash.draw('c_dette', cpParProgramme('traj', 'dette_pib', ' %', true, 'bas', { dec: 0 }));
dash.draw('c_deficit', cpParProgramme('traj', 'deficit', ' %', true, 'bas'));
dash.draw('c_primaire', cpParProgramme('traj', 'solde_primaire_pib', ' %', true, 'haut'));
dash.draw('c_esp', (el) => {
  const d = dash.data('traj');
  if (!cpPret(el, d)) return;
  cpLignes(el, cpProgrammes().filter((x) => x !== CP_SQ).map((prog) => cpSerie(d, prog, 'ecart_solde_primaire_pib')), ' pt', true, 'haut', 2);
});
dash.draw('c_depenses', (el) => {
  const d = dash.data('traj');
  if (!cpPret(el, d)) return;
  const prog = cpProgDetail();
  const s = [];
  for (const pr of [CP_SQ, prog]) {
    s.push({ ...cpSerie(d, pr, 'depenses_primaires_pib', { suffixe: ' : dépenses hors intérêts', tirets: false }) });
    s.push({ ...cpSerie(d, pr, 'recettes_pib', { suffixe: ' : recettes', tirets: true }) });
  }
  cpLignes(el, s, ' %', false, null);
});

// décomposition du déficit
window.cpAnneeDette = () => cpProche([2032, 2037, 2050]);
dash.draw('v_annee', (el) => { el.textContent = String(cpAnneeDette()); });
const decompVal = (el, prog, comp, champ) => {
  const d = dash.data('decomposition');
  const p = cpParams(), an = cpAnneeDette();
  if (d.status !== 'ok' || !prog) { el.textContent = '—'; return; }
  el.dataset.where = `programme=${encodeURIComponent(prog)}&scenario=${encodeURIComponent(p.scenario)}&annee=${an}&comparaison=${comp}`;
  const r = d.data.find((x) => x.programme === prog && x.scenario === p.scenario && Number(x.annee) === an && x.comparaison === comp);
  el.textContent = r ? cpSigne(Number(r[champ]), 2) : '—';
};
dash.draw('d_sq_total', (el) => decompVal(el, CP_SQ, 'depuis_2029', 'ecart_deficit'));
dash.draw('d_sq_prim', (el) => decompVal(el, CP_SQ, 'depuis_2029', 'primaire'));
dash.draw('d_prog_total', (el) => decompVal(el, cpProgDetail(), 'ecart_statu_quo', 'ecart_deficit'));
const PARTS_DETTE = [['primaire', 'Déficit primaire'], ['taux', 'Taux hors prime'], ['prime_dette', 'Prime de dette'],
  ['accumulation_dette', 'Dette en plus'], ['croissance', 'PIB différent'], ['autres', 'Autres intérêts']];
dash.draw('c_decomp', (el) => {
  const d = dash.data('decomposition');
  if (!cpPret(el, d)) return;
  const p = cpParams(), prog = cpProgDetail(), an = cpAnneeDette();
  const r = d.data.find((x) => x.programme === prog && x.scenario === p.scenario && Number(x.annee) === an && x.comparaison === 'ecart_statu_quo');
  if (!r) { el.replaceChildren(); return; }
  const rows = PARTS_DETTE.map(([k, nom]) => ({ nom, v: Number(r[k]), lab: `${cpSigne(Number(r[k]), 2)} pt` }))
    .filter((x) => x.nom !== 'Autres intérêts' || Math.abs(x.v) >= 0.005);
  cpBarres(el, rows, { bon: 'negatif', aria: `Écart de déficit de ${prog} avec le statu quo en ${an}, par composante` });
});
