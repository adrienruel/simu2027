"""Page publique du comparateur (roadmap du comparateur, phase 9.3, 18/11/2026).

Lit les sorties du comparateur (sorties/comparaison_*.csv, sources_poids.csv) et écrit une page HTML autonome,
sans le dépôt pour la lire : sorties/comparateur.html. Aucun calcul : la page ne montre que ce que les sorties
publient (manifeste), avec, pour chaque chiffre, la mesure, le paramètre ou la source qui le produit.

    python -m outils.page_comparateur
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict

from moteur.parametres import RACINE, Parametres

S = RACINE / "sorties"
ANNEE = 2037
ANNEES_COURBES = range(2029, 2061)


def _lire(nom):
    with (S / nom).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def donnees() -> dict:
    p = Parametres()
    traj = defaultdict(lambda: defaultdict(dict))
    for r in _lire("comparaison_trajectoire.csv"):
        t = int(r["annee"])
        if t in ANNEES_COURBES:
            traj[r["programme"]][r["scenario"]][t] = [float(r["deficit"]), float(r["dette_pib"]),
                                                      float(r["ecart_solde_primaire_pib"]), int(r["hors_plausibilite"])]
    mc = defaultdict(dict)
    for r in _lire("comparaison_incertitude.csv"):
        if r["grandeur"] == "deficit" and int(r["annee"]) == ANNEE:
            mc[r["programme"]][r["rho"]] = {"p10": float(r["p10"]), "p50": float(r["p50"]), "p90": float(r["p90"]),
                                            "proba": float(r["proba_mieux_que_statu_quo"]) if r["proba_mieux_que_statu_quo"] else None}
    mes = defaultdict(list)
    for r in _lire("comparaison_mesures.csv"):
        if r["scenario"] == "Prudent" and int(r["annee"]) == ANNEE and r["nature"] == "mesure" and r["programme"] != "Statu quo":
            mes[r["programme"]].append({"m": r["mesure"], "g": r["groupe"], "md": float(r["md"])})
    mes = {k: sorted(v, key=lambda x: -abs(x["md"]))[:10] for k, v in mes.items()}
    red = {}
    for r in _lire("comparaison_redistribution.csv"):
        if int(r["annee"]) == 2032 and r["programme"] != "Statu quo":
            red[r["programme"]] = {"couverture": float(r["couverture_menages_pct"]), "publies": r["deciles_publies"] == "1",
                                   "pauvrete": float(r["pauvrete_pct"]) - float(r["pauvrete_pct_sq"]),
                                   "gini": float(r["gini"]) - float(r["gini_sq"])}
    dec = defaultdict(list)
    for r in _lire("comparaison_redistribution_deciles.csv"):
        if int(r["annee"]) == 2032:
            dec[r["programme"]].append(float(r["variation_pct"]))
    sources = [{"cle": r["cle"], "poids": float(r["deficit_2037"]), "url": r["url"], "source": r["source"]}
               for r in _lire("sources_poids.csv")[:15]]
    lect = sorted(_lire("comparaison_lectures.csv"), key=lambda r: -abs(float(r["poids_2037"] or 0)))[:10]
    lectures = [{"programme": r["programme"], "lecture": r["lecture"], "poids": float(r["poids_2037"]), "statut": r["statut"],
                 "source": r["source"]} for r in lect]
    return {"annee": ANNEE, "seuil_dette": p.val("publication.seuil_dette_plausible"),
            "seuil_deciles": p.val("publication.seuil_couverture_deciles") * 100,
            "traj": traj, "mc": mc, "mesures": mes, "redistribution": red, "deciles": dec,
            "sources": sources, "lectures": lectures}


PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparateur des programmes 2027</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* Plan : une colonne de lecture (synthèse, courbes, détail d'un programme, hypothèses) ; encre bleu de Prusse sur gris froid. */
:root {
  --fond: #f6f7f8; --carte: #ffffff; --encre: #14171c; --encre-2: #4d5560; --trait: #d9dde2;
  --accent: #2a78d6; --accent-doux: rgba(42,120,214,.12); --bon: #1a7f45; --mauvais: #b3402f;
  --gris-serie: #b6bcc4; --hors: #9aa1aa;
  --titre: "Newsreader", Georgia, serif; --texte: "IBM Plex Sans", system-ui, sans-serif;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --fond: #121417; --carte: #1a1d21; --encre: #eceef1; --encre-2: #a9b0b9; --trait: #30353c;
    --accent: #3987e5; --accent-doux: rgba(57,135,229,.18); --bon: #4cbf7c; --mauvais: #e5806f; --gris-serie: #4a5058; --hors: #6b727b; color-scheme: dark; }
}
:root[data-theme="dark"] { --fond: #121417; --carte: #1a1d21; --encre: #eceef1; --encre-2: #a9b0b9; --trait: #30353c;
  --accent: #3987e5; --accent-doux: rgba(57,135,229,.18); --bon: #4cbf7c; --mauvais: #e5806f; --gris-serie: #4a5058; --hors: #6b727b; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--fond); color: var(--encre); font: 15px/1.55 var(--texte); }
main { max-width: 980px; margin: 0 auto; padding: 32px 20px 64px; display: grid; gap: 28px; }
h1, h2 { font-family: var(--titre); font-weight: 600; text-wrap: balance; margin: 0; }
h1 { font-size: 34px; line-height: 1.15; }
h2 { font-size: 23px; }
p { margin: 0; max-width: 68ch; }
.sous { color: var(--encre-2); }
section { display: grid; gap: 14px; }
.carte { background: var(--carte); border: 1px solid var(--trait); border-radius: 10px; padding: 18px 20px; }
.avertir { border-left: 4px solid var(--accent); display: grid; gap: 6px; }
.avertir ul { margin: 0; padding-left: 18px; display: grid; gap: 4px; }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--trait); vertical-align: top; }
th { font-weight: 600; font-size: 13px; color: var(--encre-2); }
td.n, th.n { text-align: right; white-space: nowrap; }
td:first-child { min-width: 170px; }
tr.choisi td { background: var(--accent-doux); }
tbody tr { cursor: pointer; }
tbody tr:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.defile { overflow-x: auto; }
.bon { color: var(--bon); } .mauvais { color: var(--mauvais); }
.puce { display: inline-block; font-size: 12px; padding: 1px 7px; border-radius: 99px; border: 1px solid var(--trait); color: var(--encre-2); }
.controles { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
select, button { font: inherit; color: var(--encre); background: var(--carte); border: 1px solid var(--trait); border-radius: 6px; padding: 5px 10px; }
button[aria-pressed="true"] { border-color: var(--accent); background: var(--accent-doux); }
select:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.graphes { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 720px) { .graphes { grid-template-columns: 1fr; } h1 { font-size: 27px; } }
svg { width: 100%; height: auto; display: block; }
svg text { fill: var(--encre-2); font: 11.5px var(--texte); }
.legende { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: var(--encre-2); }
.legende i { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 6px; }
.bulle { position: fixed; pointer-events: none; background: var(--carte); border: 1px solid var(--trait); border-radius: 6px;
  padding: 6px 9px; font-size: 13px; box-shadow: 0 4px 14px rgba(0,0,0,.12); display: none; font-variant-numeric: tabular-nums; }
a { color: var(--accent); }
footer { color: var(--encre-2); font-size: 13px; }
</style>
</head>
<body>
<main>
<header style="display:grid;gap:8px">
  <h1>Comparateur des programmes 2027</h1>
  <p class="sous">Douze programmes chiffrés sur un même moteur, contre un statu quo (législation du PLF 2027, puis aucune mesure nouvelle). Mêmes règles pour tous : on ne reprend que les mesures, jamais les économies annoncées.</p>
</header>

<div class="carte avertir" role="note">
  <strong>À lire avant les chiffres</strong>
  <ul>
    <li>Le scénario prudent n'est pas un scénario central : c'est une borne basse raisonnable. Le médian est à côté.</li>
    <li>La mesure robuste est l'écart de solde primaire au statu quo : elle ne dépend pas de l'emballement des intérêts. Les niveaux de déficit et de dette après 2037 ne sont pas des prévisions.</li>
    <li>Au-delà de <span id="seuil-dette"></span> % de dette, une trajectoire n'a plus valeur de prévision : ces années sont en gris.</li>
    <li>Programmes marqués « partiel » : leur document complet n'est pas publié.</li>
    <li>Déciles de niveau de vie publiés seulement si la microsimulation couvre au moins <span id="seuil-dec"></span> % du budget « ménages » du programme.</li>
  </ul>
</div>

<section aria-labelledby="t-synthese">
  <h2 id="t-synthese">Synthèse en <span class="an"></span></h2>
  <p class="sous">Classement sur l'écart de solde primaire au statu quo (points de PIB, positif = meilleur que le statu quo), déficit public et fourchette du calcul d'incertitude (600 tirages par borne, 10e et 90e centiles, hypothèses indépendantes ou liées). Cliquez sur une ligne pour la suivre dans les courbes et le détail.</p>
  <div class="carte defile"><table id="synthese"><thead><tr>
    <th>Programme</th><th class="n">Écart de solde<br>primaire, prudent</th><th class="n">Écart,<br>médian</th>
    <th class="n">Déficit,<br>prudent</th><th class="n">Fourchette<br>du déficit</th><th class="n">Mieux que le<br>statu quo</th><th class="n">Dette,<br>prudent</th>
  </tr></thead><tbody></tbody></table></div>
</section>

<section aria-labelledby="t-courbes">
  <h2 id="t-courbes">Trajectoires jusqu'en 2060</h2>
  <div class="controles">
    <label for="scen">Scénario</label>
    <select id="scen"><option>Prudent</option><option>Médian</option><option>Crise</option><option>Optimiste</option></select>
    <label for="prog">Programme suivi</label><select id="prog"></select>
  </div>
  <div class="legende"><span><i style="border-color:var(--accent)"></i><span id="leg-prog"></span></span><span><i style="border-color:var(--encre);border-top-style:dashed"></i>Statu quo</span><span><i style="border-color:var(--gris-serie)"></i>Autres programmes</span><span><i style="border-color:var(--hors)"></i>Au-delà du seuil de plausibilité</span></div>
  <div class="graphes">
    <div class="carte" style="display:grid;gap:4px;align-content:start"><strong>Déficit public (% du PIB)</strong><span class="sous" style="font-size:13px">Échelle limitée aux années plausibles.</span><svg id="g-deficit" viewBox="0 0 440 260" role="img" aria-label="Déficit public par année"></svg></div>
    <div class="carte" style="display:grid;gap:4px;align-content:start"><strong>Dette publique (% du PIB)</strong><svg id="g-dette" viewBox="0 0 440 260" role="img" aria-label="Dette publique par année"></svg></div>
  </div>
</section>

<section aria-labelledby="t-detail">
  <h2 id="t-detail">Ce qui fait le chiffre : <span id="nom-detail"></span></h2>
  <div class="graphes">
    <div class="carte"><strong>Dix mesures les plus lourdes en <span class="an"></span>, prudent (Md€ de 2026, signe du solde)</strong><div class="defile"><table id="mesures"><tbody></tbody></table></div></div>
    <div class="carte" style="display:grid;gap:10px;align-content:start"><strong>Redistribution en 2032</strong><div id="redis"></div><svg id="g-deciles" viewBox="0 0 440 200" role="img" aria-label="Variation du niveau de vie par décile"></svg></div>
  </div>
</section>

<section aria-labelledby="t-hyp">
  <h2 id="t-hyp">Les hypothèses qui pèsent le plus</h2>
  <p class="sous">Lectures de programme à valider en priorité (ce que la lecture change à l'écart de solde primaire en <span class="an"></span>, points de PIB), puis les paramètres sourcés classés par poids, avec leur source.</p>
  <div class="carte defile"><table id="lectures"><thead><tr><th>Programme</th><th>Lecture</th><th class="n">Poids (points)</th><th>Statut</th><th>Source</th></tr></thead><tbody></tbody></table></div>
  <div class="carte defile"><table id="sources"><thead><tr><th>Paramètre</th><th class="n">Poids sur le déficit</th><th>Source</th></tr></thead><tbody></tbody></table></div>
</section>

<footer>Sorties du dépôt <a href="https://github.com/adrienruel/simu2027">adrienruel/simu2027</a> (fichiers sorties/comparaison_*.csv, tracés par sorties/MANIFESTE.json). Méthode et décisions : docs/journal.md.</footer>
</main>
<div class="bulle" id="bulle"></div>
<script>
const D = __DONNEES__;
const A = D.annee, $ = s => document.querySelector(s);
const fmt = (x, d = 1) => x == null ? "–" : x.toLocaleString("fr-FR", {minimumFractionDigits: d, maximumFractionDigits: d});
const signe = x => (x > 0 ? "+" : "") + fmt(x, 2);
document.querySelectorAll(".an").forEach(e => e.textContent = A);
$("#seuil-dette").textContent = D.seuil_dette; $("#seuil-dec").textContent = D.seuil_deciles;
const progs = Object.keys(D.traj).filter(p => p !== "Statu quo");
const v = (p, s, t, i) => (D.traj[p][s][t] || [])[i];
progs.sort((a, b) => v(b, "Prudent", A, 2) - v(a, "Prudent", A, 2));
let choisi = progs[0];
let enregistre = null; try { enregistre = localStorage.getItem("simu2027-prog"); } catch (e) {}
if (enregistre && progs.includes(enregistre)) choisi = enregistre;

function synthese() {
  const tb = $("#synthese tbody"); tb.innerHTML = "";
  for (const p of progs) {
    const m0 = (D.mc[p] || {})["0"], m1 = (D.mc[p] || {})["1"];
    const lo = m0 && m1 ? Math.min(m0.p10, m1.p10) : null, hi = m0 && m1 ? Math.max(m0.p90, m1.p90) : null;
    const pr = m0 && m1 ? [m0.proba, m1.proba].sort((a, b) => a - b) : null;
    const e = v(p, "Prudent", A, 2), em = v(p, "Médian", A, 2);
    const tr = document.createElement("tr"); tr.tabIndex = 0; if (p === choisi) tr.className = "choisi";
    tr.innerHTML = `<td>${p.replace(" — partiel", ' <span class="puce">partiel</span>')}</td>
      <td class="n ${e >= 0 ? "bon" : "mauvais"}">${signe(e)}</td><td class="n">${signe(em)}</td>
      <td class="n">${fmt(v(p, "Prudent", A, 0), 2)} %</td><td class="n">${lo == null ? "–" : fmt(lo) + " à " + fmt(hi) + " %"}</td>
      <td class="n">${pr ? Math.round(pr[0] * 100) + " à " + Math.round(pr[1] * 100) + " %" : "–"}</td>
      <td class="n">${fmt(v(p, "Prudent", A, 1), 0)} %</td>`;
    const go = () => choisir(p); tr.onclick = go; tr.onkeydown = ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); } };
    tb.appendChild(tr);
  }
  const sq = document.createElement("tr"); sq.style.cursor = "default";
  sq.innerHTML = `<td>Statu quo</td><td class="n">0,00</td><td class="n">0,00</td><td class="n">${fmt(v("Statu quo", "Prudent", A, 0), 2)} %</td><td class="n">–</td><td class="n">–</td><td class="n">${fmt(v("Statu quo", "Prudent", A, 1), 0)} %</td>`;
  tb.appendChild(sq);
}

const bulle = $("#bulle");
function courbe(svg, i, unite) {
  const s = $("#scen").value, W = 440, H = 260, g = 44, d = 12, h = 22, b = 30;
  const ans = Object.keys(D.traj["Statu quo"][s]).map(Number).sort((a, b) => a - b);
  // échelle sur les années plausibles (dette sous le seuil) : au-delà, les courbes sortent du cadre, en gris
  const tous = [...progs, "Statu quo"].flatMap(p => ans.filter(t => !v(p, s, t, 3)).map(t => v(p, s, t, i))).filter(x => x != null);
  let lo = Math.min(0, ...tous), hi = Math.max(...tous) * 1.05;
  const brut = (hi - lo) / 5, mag = 10 ** Math.floor(Math.log10(brut)), pas = [1, 2, 2.5, 5, 10].map(k => k * mag).find(k => k >= brut);
  lo = Math.floor(lo / pas) * pas; hi = Math.ceil(hi / pas) * pas;
  const X = t => g + (t - ans[0]) / (ans.at(-1) - ans[0]) * (W - g - d), Y = y => h + (hi - y) / (hi - lo) * (H - h - b);
  const id = svg.id + "-cadre";
  let o = `<defs><clipPath id="${id}"><rect x="${g}" y="${h - 2}" width="${W - g - d}" height="${H - h - b + 4}"/></clipPath></defs>`;
  for (let y = lo; y <= hi + 1e-9; y += pas) o += `<line x1="${g}" x2="${W - d}" y1="${Y(y)}" y2="${Y(y)}" stroke="var(--trait)" stroke-width="1"/><text x="${g - 6}" y="${Y(y) + 4}" text-anchor="end">${y}</text>`;
  for (const t of [2030, 2040, 2050, 2060]) o += `<text x="${X(t)}" y="${H - 10}" text-anchor="middle">${t}</text>`;
  const trace = (p, couleur, large, tirets) => {
    let seg = "", hors = "";
    ans.forEach((t, k) => { const x = X(t), y = Y(v(p, s, t, i)), dans = !v(p, s, t, 3);
      if (k === 0) { seg += `M${x} ${y}`; return; }
      const pt = `L${x} ${y}`;
      if (dans) seg += pt; else { hors += (hors ? "" : `M${X(ans[k - 1])} ${Y(v(p, s, ans[k - 1], i))}`) + pt; } });
    return `<path d="${seg}" fill="none" stroke="${couleur}" stroke-width="${large}" ${tirets ? 'stroke-dasharray="5 4"' : ""} stroke-linejoin="round"/>` +
           (hors ? `<path d="${hors}" fill="none" stroke="var(--hors)" stroke-width="${large}" ${tirets ? 'stroke-dasharray="5 4"' : ""} opacity=".8"/>` : "");
  };
  o += `<g clip-path="url(#${id})">`;
  for (const p of progs) if (p !== choisi) o += trace(p, "var(--gris-serie)", 1, false);
  o += trace("Statu quo", "var(--encre)", 1.5, true) + trace(choisi, "var(--accent)", 2.5, false);
  const fin = ans.at(-1), dern = [...ans].reverse().find(t => !v(choisi, s, t, 3)) || ans[0];
  o += `<circle cx="${X(dern)}" cy="${Y(v(choisi, s, dern, i))}" r="4" fill="var(--accent)" stroke="var(--carte)" stroke-width="2"/></g>`;
  o += `<line class="croix" x1="0" x2="0" y1="${h}" y2="${H - b}" stroke="var(--encre-2)" stroke-width="1" opacity="0"/>`;
  o += `<rect x="${g}" y="${h}" width="${W - g - d}" height="${H - h - b}" fill="transparent"/>`;
  svg.innerHTML = o;
  const croix = svg.querySelector(".croix"), zone = svg.querySelector("rect");
  zone.onmousemove = ev => { const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width * W;
    const t = Math.round(ans[0] + (x - g) / (W - g - d) * (fin - ans[0])); if (t < ans[0] || t > fin) return;
    croix.setAttribute("x1", X(t)); croix.setAttribute("x2", X(t)); croix.setAttribute("opacity", ".5");
    bulle.innerHTML = `<strong>${t}</strong>, ${s.toLowerCase()}<br>${choisi.replace(" — partiel", "")} : ${fmt(v(choisi, s, t, i))} ${unite}<br>Statu quo : ${fmt(v("Statu quo", s, t, i))} ${unite}` + (v(choisi, s, t, 3) ? "<br><em>au-delà du seuil de plausibilité</em>" : "");
    bulle.style.display = "block"; bulle.style.left = Math.min(ev.clientX + 14, innerWidth - 240) + "px"; bulle.style.top = (ev.clientY + 14) + "px"; };
  zone.onmouseleave = () => { croix.setAttribute("opacity", "0"); bulle.style.display = "none"; };
}

function detail() {
  $("#nom-detail").textContent = choisi; $("#leg-prog").textContent = choisi;
  const tb = $("#mesures tbody"); tb.innerHTML = "";
  for (const m of D.mesures[choisi] || []) {
    const solde = m.g === "Recettes" ? m.md : -m.md;
    const tr = document.createElement("tr"); tr.style.cursor = "default";
    tr.innerHTML = `<td>${m.m}</td><td class="n ${solde >= 0 ? "bon" : "mauvais"}">${solde > 0 ? "+" : ""}${fmt(solde)}</td>`; tb.appendChild(tr);
  }
  const r = D.redistribution[choisi], svg = $("#g-deciles");
  if (!r) { $("#redis").textContent = "Pas de microsimulation pour ce programme."; svg.style.display = "none"; return; }
  $("#redis").innerHTML = `<p>Mesures codées dans la microsimulation : <strong>${fmt(r.couverture, 0)} %</strong> du budget « ménages » (seuil ${D.seuil_deciles} %). Taux de pauvreté ${signe(r.pauvrete)} point, Gini ${r.gini > 0 ? "+" : ""}${fmt(r.gini, 3)}, par rapport à la législation actuelle sur la même population.</p>`;
  const dec = D.deciles[choisi];
  if (!r.publies || !dec) { svg.style.display = "none"; $("#redis").insertAdjacentHTML("beforeend", '<p class="sous">Déciles non publiés : la couverture est sous le seuil.</p>'); return; }
  svg.style.display = ""; $("#redis").insertAdjacentHTML("beforeend", '<p class="sous">Variation du niveau de vie par décile (%), mesures codées seulement.</p>');
  const W = 440, H = 200, g = 40, h = 14, b = 28, m = Math.max(1, ...dec.map(Math.abs)), lo = Math.min(0, ...dec) < 0 ? -m : 0;
  const Y = y => h + (m - y) / (m - lo) * (H - h - b), bw = (W - g - 10) / 10;
  let o = `<line x1="${g}" x2="${W - 10}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--encre-2)"/>`;
  [m, lo].forEach(y => o += `<text x="${g - 6}" y="${Y(y) + 4}" text-anchor="end">${fmt(y)} %</text>`);
  dec.forEach((x, k) => { const x0 = g + k * bw + 3, y0 = Math.min(Y(0), Y(x)), hh = Math.abs(Y(x) - Y(0));
    o += `<rect x="${x0}" y="${y0}" width="${bw - 6}" height="${Math.max(hh, 1)}" rx="3" fill="var(--accent)"><title>Décile ${k + 1} : ${fmt(x, 2)} %</title></rect><text x="${x0 + (bw - 6) / 2}" y="${H - 10}" text-anchor="middle">D${k + 1}</text>`; });
  svg.innerHTML = o;
}

function hypotheses() {
  const tl = $("#lectures tbody");
  for (const l of D.lectures) { const tr = document.createElement("tr"); tr.style.cursor = "default";
    tr.innerHTML = `<td>${l.programme}</td><td>${l.lecture}</td><td class="n">${signe(l.poids)}</td><td><span class="puce">${l.statut}</span></td><td>${l.source}</td>`; tl.appendChild(tr); }
  const ts = $("#sources tbody");
  for (const x of D.sources) { const tr = document.createElement("tr"); tr.style.cursor = "default";
    const src = x.url ? `<a href="${x.url}">${x.source}</a>` : x.source;
    tr.innerHTML = `<td><code>${x.cle}</code></td><td class="n">${fmt(x.poids, 2)}</td><td>${src}</td>`; ts.appendChild(tr); }
}

function choisir(p) { choisi = p; try { localStorage.setItem("simu2027-prog", p); } catch (e) {} $("#prog").value = p; tout(); }
function tout() { synthese(); courbe($("#g-deficit"), 0, "%"); courbe($("#g-dette"), 1, "%"); detail(); }
for (const p of progs) { const o = document.createElement("option"); o.textContent = p; $("#prog").appendChild(o); }
$("#prog").value = choisi; $("#prog").onchange = e => choisir(e.target.value); $("#scen").onchange = tout;
hypotheses(); tout();
</script>
</body>
</html>
"""


def main() -> None:
    from outils import trace
    d = donnees()
    html = PAGE.replace("__DONNEES__", json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    f = S / "comparateur.html"
    f.write_text(html, encoding="utf-8")
    trace.enregistrer(f.name, script="outils.page_comparateur")
    print(f"Écrit : {f} ({len(html) // 1024} Ko)")


if __name__ == "__main__":
    main()
