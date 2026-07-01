"""Moteur financier MINDVEST.

Tous les calculs sont des ESTIMATIONS pédagogiques (hypothèses simplifiées).
Aucune de ces fonctions ne constitue un conseil en investissement.
"""
from __future__ import annotations

import math
from typing import Any

# Catégories de patrimoine reconnues (pour l'agrégation et les graphes).
CATEGORIES = ["Immobilier", "PEA", "Assurance-Vie", "Livrets", "Actions", "Crypto", "Autres"]

# Catégories considérées comme "épargne de précaution" mobilisable rapidement.
LIQUID_CATEGORIES = {"Livrets"}


# ─── Bases ───────────────────────────────────────────────────────────

def marge_mensuelle(profile: dict[str, Any]) -> float:
    """Salaire net - charges fixes. Retourne 0 si données manquantes."""
    sal = profile.get("salaire_net") or 0
    charges = profile.get("charges_fixes") or 0
    return max(0.0, float(sal) - float(charges))


def patrimoine_total(assets: list[dict[str, Any]]) -> float:
    return float(sum((a.get("montant") or 0) for a in assets))


def repartition(assets: list[dict[str, Any]]) -> dict[str, float]:
    """Somme des montants par catégorie (catégories non nulles uniquement)."""
    agg: dict[str, float] = {}
    for a in assets:
        cat = a.get("categorie") or "Autres"
        agg[cat] = agg.get(cat, 0.0) + float(a.get("montant") or 0)
    return {k: v for k, v in agg.items() if v > 0}


def epargne_precaution_actuelle(assets: list[dict[str, Any]]) -> float:
    return float(
        sum((a.get("montant") or 0) for a in assets
            if (a.get("categorie") in LIQUID_CATEGORIES))
    )


def diversification_score(assets: list[dict[str, Any]]) -> int:
    """Score 0-100 basé sur l'indice de Herfindahl (concentration).

    100 = parfaitement diversifié entre les catégories présentes ;
    faible = tout le patrimoine sur un seul actif.
    """
    rep = repartition(assets)
    total = sum(rep.values())
    if total <= 0 or len(rep) <= 1:
        return 0 if total <= 0 else 25
    shares = [v / total for v in rep.values()]
    hhi = sum(s * s for s in shares)          # 1/n (diversifié) .. 1 (concentré)
    n = len(shares)
    best = 1.0 / n
    # Normalise entre best (=score 100) et 1 (=score 0).
    score = (1 - hhi) / (1 - best) * 100 if n > 1 else 0
    return int(max(0, min(100, round(score))))


def rendement_moyen_pondere(assets: list[dict[str, Any]]) -> float:
    """Rendement annuel moyen pondéré par les montants (en %)."""
    total = patrimoine_total(assets)
    if total <= 0:
        return 0.0
    return sum((a.get("montant") or 0) * (a.get("perf") or 0) for a in assets) / total


# ─── Profil de risque ────────────────────────────────────────────────

def risk_label(score: int) -> str:
    if score <= 2:
        return "Très prudent"
    if score <= 4:
        return "Prudent"
    if score <= 6:
        return "Modéré"
    if score <= 8:
        return "Dynamique"
    return "Offensif"


def allocation_cible(score: int) -> tuple[int, int]:
    """(part actions %, part obligations/fonds euros %) selon le score de risque."""
    actions = int(max(20, min(90, round(20 + score * 7))))
    return actions, 100 - actions


def rendement_attendu(score: int) -> float:
    """Rendement annuel réel attendu (fraction), 2 %..8 % selon le risque."""
    return 0.02 + (score / 10.0) * 0.06


# ─── Simulateur de crédit ────────────────────────────────────────────

def mensualite(capital: float, taux_annuel: float, annees: int) -> float:
    """Mensualité d'un crédit amortissable (formule d'annuité)."""
    if capital <= 0:
        return 0.0
    n = annees * 12
    r = taux_annuel / 12.0
    if r == 0:
        return capital / n
    return capital * r / (1 - (1 + r) ** (-n))


def simulation_credit(prix: float, apport: float, taux: float, annees: int,
                      assurance_taux: float = 0.0045) -> dict[str, float]:
    """Détaille un crédit immobilier : mensualité, coût, total remboursé."""
    emprunt = max(0.0, prix - apport)
    m = mensualite(emprunt, taux, annees)
    assurance_mens = emprunt * assurance_taux / 12.0
    n = annees * 12
    total_rembourse = m * n
    cout_interets = total_rembourse - emprunt
    return {
        "emprunt": emprunt,
        "mensualite": m,
        "assurance_mensuelle": assurance_mens,
        "mensualite_totale": m + assurance_mens,
        "cout_interets": cout_interets,
        "total_rembourse": total_rembourse,
        "assurance_totale": assurance_mens * n,
    }


def taux_endettement(mensualite_totale: float, salaire_net: float) -> float:
    if not salaire_net:
        return 0.0
    return mensualite_totale / salaire_net * 100.0


# ─── Épargne de précaution ───────────────────────────────────────────

def diagnostic_precaution(actuel: float, charges_fixes: float,
                          mensualite_epargne: float = 200.0) -> dict[str, Any]:
    cible = 3 * (charges_fixes or 0)
    manque = max(0.0, cible - actuel)
    if cible <= 0:
        statut = "inconnu"
    elif actuel >= cible:
        statut = "ok"
    elif actuel >= 0.5 * cible:
        statut = "en_cours"
    else:
        statut = "critique"
    mois = math.ceil(manque / mensualite_epargne) if mensualite_epargne > 0 and manque > 0 else 0
    pct = (actuel / cible * 100.0) if cible > 0 else 0.0
    return {
        "cible": cible, "actuel": actuel, "manque": manque,
        "statut": statut, "mois_pour_completer": mois, "pct": min(100.0, pct),
    }


# ─── Moteur de stratégie ─────────────────────────────────────────────

def strategie(profile: dict[str, Any]) -> dict[str, Any]:
    """Construit la stratégie patrimoniale personnalisée (liste d'étapes)."""
    assets = profile.get("patrimoine", [])
    charges = profile.get("charges_fixes") or 0
    marge = marge_mensuelle(profile)
    score = profile.get("profil_risque", 5)
    precaution = epargne_precaution_actuelle(assets)
    diag = diagnostic_precaution(precaution, charges)

    # ── Étape 1 : épargne de précaution ──
    step_precaution = {
        "titre": "Épargne de précaution",
        "statut": {"critique": "crit", "en_cours": "warn", "ok": "ok"}.get(diag["statut"], "soon"),
        "badge": {"critique": "🔴 Critique", "en_cours": "⚠️ En cours", "ok": "✅ Constituée"}
                 .get(diag["statut"], "À évaluer"),
        "diag": diag,
    }

    # ── Étape 2 : projet immobilier ──
    projet = profile.get("projet_immo")
    budget = profile.get("budget_immo") or 0
    step_immo = None
    if projet and projet != "Non" and budget > 0:
        apport_cible = budget * 0.20
        apport_actuel = min(apport_cible, precaution * 0.5)  # part mobilisable
        manque = max(0.0, apport_cible - apport_actuel)
        urgent = projet in ("2-5 ans", "<2 ans")
        step_immo = {
            "titre": "Projet immobilier",
            "statut": "warn" if urgent else "soon",
            "badge": ("🟠 Important" if urgent else "🔵 À venir"),
            "budget": budget,
            "apport_cible": apport_cible,
            "apport_actuel": apport_actuel,
            "manque": manque,
            "pct": (apport_actuel / apport_cible * 100.0) if apport_cible else 0.0,
            "horizon": projet,
        }

    # ── Étape 3 : structure d'investissement ──
    actions, oblig = allocation_cible(score)
    step_invest = {
        "titre": "Structure d'investissement",
        "statut": "ok",
        "badge": "🟢 Après la précaution",
        "actions_pct": actions,
        "obligations_pct": oblig,
        "esg": profile.get("esg", False),
        "risk_label": risk_label(score),
    }

    # ── Étape 4 : répartition mensuelle de la marge ──
    reste = marge
    alloc = {}
    if diag["statut"] in ("critique", "en_cours"):
        p = min(reste, 200.0)
        alloc["Épargne précaution"] = p
        reste -= p
    if step_immo and step_immo["manque"] > 0:
        p = min(reste, max(0.0, reste * 0.6))
        alloc["Apport immobilier"] = round(p)
        reste -= p
    invest = min(reste, max(0.0, reste * 0.75))
    if invest > 0:
        alloc["Investissement PEA/AV"] = round(invest)
        reste -= invest
    if reste > 0:
        alloc["Réserve flexible"] = round(reste)

    step_alloc = {"titre": "Répartition mensuelle", "marge": marge, "allocation": alloc}

    return {
        "marge": marge,
        "steps": [s for s in [step_precaution, step_immo, step_invest, step_alloc] if s],
        "precaution": step_precaution,
        "immo": step_immo,
        "invest": step_invest,
        "alloc": step_alloc,
    }


def projection(profile: dict[str, Any], annees: int = 10,
               invest_mensuel: float | None = None) -> dict[str, list[float]]:
    """Projette le patrimoine sur N années.

    Hypothèses : rendement financier selon le profil de risque appliqué à la
    part non-immobilière + versements mensuels ; immobilier apprécié à 3,5 %/an.
    """
    assets = profile.get("patrimoine", [])
    rep = repartition(assets)
    immo = rep.get("Immobilier", 0.0)
    financier = patrimoine_total(assets) - immo
    r_fin = rendement_attendu(profile.get("profil_risque", 5))
    r_immo = 0.035

    if invest_mensuel is None:
        strat = strategie(profile)
        invest_mensuel = strat["alloc"]["allocation"].get("Investissement PEA/AV", 0.0)

    xs = list(range(annees + 1))
    total, part_immo, part_fin = [], [], []
    fin, im = financier, immo
    for year in xs:
        total.append(fin + im)
        part_fin.append(fin)
        part_immo.append(im)
        # avance d'un an
        fin = fin * (1 + r_fin) + invest_mensuel * 12
        im = im * (1 + r_immo)
    return {"annees": xs, "total": total, "financier": part_fin, "immobilier": part_immo}
