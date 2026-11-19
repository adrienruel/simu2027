// Ménages types : ce que chaque programme change au revenu disponible de quelques ménages fictifs
window.CP_SEUIL_MICRO = 80; // % du budget « ménages » codé dans la microsimulation pour publier un total (règle des déciles)
window.cpMenage = () => {
  const d = dash.data('menages_types');
  if (d.status !== 'ok') return null;
  const ids = [...new Set(d.data.map((r) => r.menage))];
  const m = dash.params().menage;
  return ids.includes(m) ? m : (ids.includes('couple_deux_smic_deux_enfants') ? 'couple_deux_smic_deux_enfants' : ids[0]);
};
dash.calc('menages_tab', {
  inputs: ['menages_types', 'couverture_tab'],
  title: 'Ménages types et couverture',
  description: "Revenu disponible de chaque ménage type avec la législation actuelle et avec les mesures codées du programme (euros de 2026 par an et par mois), part du budget « ménages » du programme codée dans la microsimulation, et total publié seulement si cette part atteint 80 % (même règle que les déciles).",
  fn: (menages_types, couverture_tab) => {
    const cv = new Map(couverture_tab.map((r) => [r.programme, r.part_codee_pct]));
    return menages_types.map((r) => {
      const part = r.programme === 'Statu quo' ? 100 : (cv.get(r.programme) ?? 0);
      return { cle: r.cle, programme: r.programme, menage: r.menage, libelle: r.libelle, ordre: Number(r.ordre),
        actuel_mois: Math.round(Number(r.revenu_disponible_actuel) / 12), programme_mois: Math.round(Number(r.revenu_disponible) / 12), ecart_mois: Number(r.ecart_mois),
        ecart_pct: Number(r.ecart_pct), part_codee_pct: part, publie: part >= 80 };
    });
  },
});
dash.draw('f_menage', (sel) => {
  const d = dash.data('menages_types');
  const types = d.status === 'ok' ? d.data.filter((r) => r.programme === 'Statu quo').sort((a, b) => Number(a.ordre) - Number(b.ordre)) : [];
  sel.replaceChildren(...types.map((r) => new Option(r.libelle, r.menage)));
  sel.value = cpMenage() || '';
  sel.onchange = () => dash.setParams({ menage: sel.value || null });
});
dash.draw('l_menage', (el) => {
  const d = dash.data('menages_types');
  const r = d.status === 'ok' ? d.data.find((x) => x.programme === 'Statu quo' && x.menage === cpMenage()) : null;
  el.textContent = r ? r.libelle.charAt(0).toLowerCase() + r.libelle.slice(1) : '—';
});
dash.draw('mt_actuel', (el) => {
  const m = cpMenage();
  cpValeurCle(el, 'menages_tab', CP_SQ, 'actuel_mois', { cle: `${CP_SQ}|${m}`, d: 0 });
});
dash.draw('mt_prog', (el) => {
  const prog = cpProgDetail(), m = cpMenage();
  const d = dash.data('menages_tab');
  const r = d.status === 'ok' ? d.data.find((x) => x.cle === `${prog}|${m}`) : null;
  el.dataset.where = `cle=${encodeURIComponent(`${prog}|${m}`)}`;
  el.classList.remove('bon', 'mauvais');
  if (!r) { el.textContent = '—'; return; }
  if (!r.publie) { el.textContent = 'non publié'; return; }
  el.textContent = cpSigne(r.ecart_mois, 0);
  cpClasse(el, r.ecart_mois, 0, 'haut', 1);
});
dash.draw('mt_part', (el) => cpValeurCle(el, 'menages_tab', cpProgDetail(), 'part_codee_pct', { cle: `${cpProgDetail()}|${cpMenage()}`, d: 0 }));

// tous les programmes pour le ménage choisi
dash.draw('t_menages', (tb) => {
  const d = dash.data('menages_tab');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const m = cpMenage();
  const rows = d.data.filter((r) => r.menage === m && r.programme !== CP_SQ)
    .sort((a, b) => (a.publie !== b.publie ? (a.publie ? -1 : 1) : b.ecart_mois - a.ecart_mois));
  for (const r of rows) {
    const c = r.publie ? cpComparer(r.ecart_mois, 0, 'haut', 1) : '';
    cpLigneTableau(tb, r.cle, [[r.programme], [cpFmt(r.actuel_mois, 0)],
      [r.publie ? cpFmt(r.programme_mois, 0) : '—'], [r.publie ? cpSigne(r.ecart_mois, 0) : 'non publié', c],
      [r.publie ? cpSigne(r.ecart_pct, 1) + ' %' : '—', c], [cpFmt(r.part_codee_pct, 0) + ' %']],
    (r.publie ? '' : 'sq') + (r.programme === cpProgDetail() ? ' choisi' : ''));
  }
});
dash.draw('c_menages', (el) => {
  const d = dash.data('menages_tab');
  if (!cpPret(el, d)) return;
  const m = cpMenage();
  const rows = d.data.filter((r) => r.menage === m && r.programme !== CP_SQ && r.publie)
    .map((r) => ({ nom: r.programme, v: r.ecart_mois, lab: `${cpSigne(r.ecart_mois, 0)} € par mois (${cpSigne(r.ecart_pct, 1)} %)` }))
    .sort((a, b) => b.v - a.v);
  cpBarres(el, rows, { dec: 0, aria: 'Écart de revenu disponible par programme, ménage choisi' });
});

// tous les ménages pour le programme choisi
dash.draw('t_menages_prog', (tb) => {
  const d = dash.data('menages_tab');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const prog = cpProgDetail();
  const rows = d.data.filter((r) => r.programme === prog).sort((a, b) => a.ordre - b.ordre);
  for (const r of rows) {
    const c = r.publie ? cpComparer(r.ecart_mois, 0, 'haut', 1) : '';
    cpLigneTableau(tb, r.cle, [[r.libelle], [cpFmt(r.actuel_mois, 0)], [r.publie ? cpFmt(r.programme_mois, 0) : '—'],
      [r.publie ? cpSigne(r.ecart_mois, 0) : 'non publié', c], [r.publie ? cpSigne(r.ecart_pct, 1) + ' %' : '—', c]],
    r.menage === cpMenage() ? 'choisi' : '');
  }
});
// mesure par mesure, programme et ménage choisis (mesures codées seulement)
dash.draw('t_menages_mesures', (tb) => {
  const d = dash.data('menages_mesures');
  tb.replaceChildren();
  if (d.status !== 'ok') return;
  const prog = cpProgDetail(), m = cpMenage();
  const rows = d.data.filter((r) => r.programme === prog && r.menage === m).sort((a, b) => Math.abs(Number(b.ecart_mois)) - Math.abs(Number(a.ecart_mois)));
  for (const r of rows) {
    const v = Number(r.ecart_mois);
    cpLigneTableau(tb, r.cle, [[r.mesure], [cpSigne(v, 0), cpComparer(v, 0, 'haut', 0.5)]]);
  }
});
dash.onData(() => {
  const d = dash.data('menages_mesures');
  const prog = cpProgDetail(), m = cpMenage();
  const vide = d.status === 'ok' && !d.data.some((r) => r.programme === prog && r.menage === m);
  for (const el of document.querySelectorAll('.cp .mt-aucune')) el.hidden = !vide;
});
