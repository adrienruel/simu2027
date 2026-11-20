// Vue d'ensemble : chiffres clés du programme choisi, rang, écart par poste, mesures prises en compte
dash.calc('rangs', {
  inputs: ['traj'],
  title: 'Rang de chaque programme',
  description: "Rang de chaque programme (hors statu quo) sur l'écart de solde primaire au statu quo, du meilleur (1) au moins bon, par scénario et par année, et nombre de programmes classés.",
  fn: (traj) => {
    const par = new Map();
    for (const r of traj) {
      if (r.programme === 'Statu quo') continue;
      const k = r.scenario + '|' + r.annee;
      if (!par.has(k)) par.set(k, []);
      par.get(k).push(r);
    }
    const out = [];
    for (const liste of par.values()) {
      liste.sort((a, b) => Number(b.ecart_solde_primaire_pib) - Number(a.ecart_solde_primaire_pib));
      liste.forEach((r, i) => out.push({ cle: `${r.programme}|${r.scenario}|${r.annee}`, programme: r.programme, scenario: r.scenario, annee: r.annee, rang: i + 1, classes: liste.length }));
    }
    return out;
  },
});
dash.calc('croissance', {
  inputs: ['traj'],
  title: 'Croissance et écart de PIB',
  description: "Croissance du PIB d'une année sur l'autre (euros constants de 2026, en %) et écart de PIB au statu quo du même scénario (en %), par programme, scénario et année. La croissance commence en 2030 : 2029 reprend l'économie de 2026.",
  fn: (traj) => {
    const idx = new Map(traj.map((r) => [r.programme + '|' + r.scenario + '|' + r.annee, Number(r.pib_md)]));
    return traj.map((r) => {
      const an = Number(r.annee);
      const avant = idx.get(r.programme + '|' + r.scenario + '|' + (an - 1));
      const sq = idx.get('Statu quo|' + r.scenario + '|' + an);
      return {
        cle: `${r.programme}|${r.scenario}|${an}`, programme: r.programme, scenario: r.scenario, annee: an,
        croissance_pct: an >= 2030 && avant ? (Number(r.pib_md) / avant - 1) * 100 : null,
        ecart_pib_pct: sq ? (Number(r.pib_md) / sq - 1) * 100 : null,
      };
    });
  },
});
const cleSel = (prog, an) => `cle=${encodeURIComponent(`${prog}|${cpParams().scenario}|${an ?? cpParams().annee}`)}`;
const valeurCle = (el, source, prog, champ, o = {}) => {
  const d = dash.data(source);
  const p = cpParams();
  if (d.status !== 'ok' || !prog) { el.textContent = '—'; return null; }
  const an = o.annee ?? p.annee;
  const cle = o.cle || `${prog}|${p.scenario}|${an}`;
  el.dataset.where = `cle=${encodeURIComponent(cle)}`;
  const r = d.data.find((x) => x.cle === cle);
  const v = r && r[champ] != null && r[champ] !== '' ? Number(r[champ]) : null;
  el.textContent = v == null ? (o.absent || '—') : (o.signe ? cpSigne(v, o.d ?? 1) : cpFmt(v, o.d ?? 1)) + (o.suffixe || '');
  return v;
};
window.cpValeurCle = valeurCle;

// tuiles
const tuileTraj = (nom, champ, d, sens, seuil) => {
  dash.draw(nom, (el) => {
    const v = cpValeur(el, 'traj', cpProgDetail(), champ, { d });
    const r = cpLigneTraj(CP_SQ);
    cpClasse(el, v, r ? Number(r[champ]) : null, sens, seuil);
  });
  dash.draw(nom + '_sq', (el) => cpValeur(el, 'traj', CP_SQ, champ, { d }));
};
tuileTraj('r_def', 'deficit', 1, 'bas');
tuileTraj('r_dette', 'dette_pib', 0, 'bas', 0.5);
tuileTraj('r_chom', 'chomage', 1, 'bas');
tuileTraj('r_pop', 'population_millions', 1, null);
dash.draw('r_esp', (el) => { const v = cpValeur(el, 'traj', cpProgDetail(), 'ecart_solde_primaire_pib', { d: 2, signe: true }); cpClasse(el, v, 0, 'haut'); });
dash.draw('r_emploi', (el) => { const v = cpValeur(el, 'traj', cpProgDetail(), 'ecart_emploi_milliers', { d: 0, signe: true }); cpClasse(el, v, 0, 'haut', 5); });
dash.draw('r_pib', (el) => { const v = valeurCle(el, 'croissance', cpProgDetail(), 'ecart_pib_pct', { d: 1, signe: true, suffixe: ' %' }); cpClasse(el, v, 0, 'haut'); });
dash.draw('r_emi', (el) => {
  const v = valeurCle(el, 'ecologie', cpProgDetail(), 'territoriales_hab_t', { d: 2 });
  const e = dash.data('ecologie');
  const sq = e.status === 'ok' ? e.data.find((x) => x.cle === `${CP_SQ}|${cpParams().scenario}|${cpParams().annee}`) : null;
  cpClasse(el, v, sq ? Number(sq.territoriales_hab_t) : null, 'bas', 0.005);
});
dash.draw('r_emi_sq', (el) => valeurCle(el, 'ecologie', CP_SQ, 'territoriales_hab_t', { d: 2 }));
dash.draw('r_pauv_annee', (el) => { el.textContent = String(cpProche([2029, 2032, 2037, 2050])); });
dash.draw('r_pauv', (el) => {
  const prog = cpProgDetail(), an = cpProche([2029, 2032, 2037, 2050]);
  const v = valeurCle(el, 'redistribution', prog, 'pauvrete_pct', { cle: `${prog}|${an}`, absent: 'non calculé' });
  const d = dash.data('redistribution');
  const r = d.status === 'ok' ? d.data.find((x) => x.cle === `${prog}|${an}`) : null;
  cpClasse(el, v, r ? Number(r.pauvrete_pct_sq) : null, 'bas', 0.1);
});
dash.draw('r_pauv_sq', (el) => { const prog = cpProgDetail(), an = cpProche([2029, 2032, 2037, 2050]); valeurCle(el, 'redistribution', prog, 'pauvrete_pct_sq', { cle: `${prog}|${an}` }); });
dash.draw('r_rang', (el) => valeurCle(el, 'rangs', cpProgDetail(), 'rang', { d: 0 }));
dash.draw('r_classes', (el) => valeurCle(el, 'rangs', cpProgDetail(), 'classes', { d: 0 }));

// écart de déficit et barres par poste
dash.calc('ecart_deficit', {
  inputs: ['traj'],
  title: 'Écart de déficit avec le statu quo',
  description: 'Déficit du statu quo moins déficit du programme, en points de PIB, par scénario et par année (+ = moins de déficit).',
  fn: (traj) => {
    const sq = new Map();
    for (const r of traj) if (r.programme === 'Statu quo') sq.set(r.scenario + '|' + r.annee, Number(r.deficit));
    return traj.filter((r) => r.programme !== 'Statu quo').map((r) => ({
      cle: r.programme + '|' + r.scenario + '|' + r.annee, programme: r.programme, scenario: r.scenario, annee: r.annee,
      ecart: sq.get(r.scenario + '|' + r.annee) - Number(r.deficit),
    }));
  },
});
dash.draw('l_ecart', (el) => valeurCle(el, 'ecart_deficit', cpProgDetail(), 'ecart', { signe: true }));
dash.draw('c_ecarts', (el) => {
  const d = dash.data('ecarts');
  if (!cpPret(el, d)) return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee)
    .map((r) => ({ nom: r.groupe, v: Number(r.part_pib), lab: `${cpSigne(Number(r.part_pib), 2)} pt (${cpSigne(Number(r.md), 0)} Md€)` }))
    .sort((a, b) => b.v - a.v);
  cpBarres(el, rows, {
    aria: `Écart au statu quo par poste, ${prog}, ${p.annee}`,
    clic: (r) => dash.setParams({ groupe: p.groupe === r.nom ? null : r.nom }),
    attenue: (r) => p.groupe && r.nom !== p.groupe,
  });
});

// mesures prises en compte
window.cpRecherche = '';
for (const i of document.querySelectorAll('.cp .f-cherche')) i.addEventListener('input', () => { cpRecherche = i.value.trim().toLowerCase(); dash.draw('t_mesures'); });
dash.draw('f_groupe', (sel) => {
  const d = dash.data('ecarts');
  const p = cpParams(), prog = cpProgDetail();
  const g = d.status === 'ok' ? [...new Set(d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee).map((r) => r.groupe))] : [];
  sel.replaceChildren(new Option('Tous les postes', ''), ...g.map((x) => new Option(x, x)));
  sel.value = p.groupe && g.includes(p.groupe) ? p.groupe : '';
  sel.onchange = () => dash.setParams({ groupe: sel.value || null });
});
const NATURES = { budget: 'mesure', mesure: 'mesure', classement: 'classement', methode: 'méthode', effet_macro: 'effet économique', perimetre: 'périmètre' };
dash.draw('t_mesures', (tb) => {
  const d = dash.data('mesures');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const p = cpParams(), prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog && r.scenario === p.scenario && Number(r.annee) === p.annee
    && (!p.groupe || r.groupe === p.groupe) && Math.abs(Number(r.md)) >= 0.05
    && (!cpRecherche || r.mesure.toLowerCase().includes(cpRecherche)))
    .sort((a, b) => Math.abs(Number(b.md)) - Math.abs(Number(a.md)));
  for (const r of rows) {
    const md = Number(r.md), c = md > 0.05 ? 'bon' : (md < -0.05 ? 'mauvais' : '');
    cpLigneTableau(tb, r.cle, [[r.mesure], [r.groupe], [NATURES[r.nature] || r.nature], [cpSigne(md, 1), c], [cpSigne(Number(r.part_pib), 2), c]]);
  }
});
