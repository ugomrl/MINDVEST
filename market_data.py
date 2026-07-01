"""Données de marché pour MINDVEST : taux et actualités.

Stratégie : on tente une actualisation en direct (API publique BCE) quand c'est
possible, avec repli systématique sur des données de démonstration réalistes
pour que l'app fonctionne hors-ligne. Tout est mis en cache (TTL) pour ne pas
rappeler les APIs à chaque interaction.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import requests
import streamlit as st

# ─── Valeurs de repli (indicatives, mi-2026) ─────────────────────────
# À ajuster / brancher sur de vraies sources en production.
_SEED_RATES = {
    "taux_bce": 2.15,          # taux de dépôt BCE (%)
    "inflation": 1.9,          # inflation France glissante (%)
    "livret_a": 2.40,
    "ldds": 2.40,
    "livret_boost": 3.00,      # meilleur livret bancaire boosté
    "credit_immo_20ans": 3.20,
    "prix_m2_france": 3200,    # €/m² moyen France
    "source": "Données de démonstration",
}


@st.cache_data(ttl=60 * 60 * 6)  # 6 h
def get_rates() -> dict[str, Any]:
    """Retourne les taux clés. Tente la BCE en direct, sinon données de démo."""
    rates = dict(_SEED_RATES)
    rates["updated_at"] = date.today().isoformat()
    try:
        # Taux directeur (dépôt) BCE via l'API SDMX du portail de données BCE.
        url = (
            "https://data-api.ecb.europa.eu/service/data/FM/"
            "D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=1&format=csvdata"
        )
        resp = requests.get(url, timeout=4)
        if resp.ok and resp.text:
            last_line = resp.text.strip().splitlines()[-1]
            value = float(last_line.split(",")[-1])
            rates["taux_bce"] = round(value, 2)
            rates["source"] = "BCE (data-api.ecb.europa.eu) — en direct"
    except Exception:
        # Hors-ligne ou API indisponible : on garde les valeurs de démo.
        pass
    return rates


def livrets(rates: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Classement des placements d'épargne de précaution (démo)."""
    r = rates or get_rates()
    data = [
        {"medaille": "🥇", "nom": "Livret bancaire boosté", "taux": r["livret_boost"],
         "avantages": "Meilleur taux, accès immédiat", "inconvenients": "Taux promo temporaire",
         "cta": "Ouvrir un compte"},
        {"medaille": "🥈", "nom": "LDDS", "taux": r["ldds"],
         "avantages": "Intérêts exonérés d'impôt", "inconvenients": "Plafond 12 000 €",
         "cta": "Demander à sa banque"},
        {"medaille": "🥉", "nom": "Livret A", "taux": r["livret_a"],
         "avantages": "Garanti par l'État, plafond 22 950 €", "inconvenients": "Taux modéré",
         "cta": "Souvent déjà ouvert"},
    ]
    return sorted(data, key=lambda x: x["taux"], reverse=True)


def credit_banques(rates: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Grille de taux crédit immo par banque (démo, autour du taux marché)."""
    r = rates or get_rates()
    base = r["credit_immo_20ans"]
    grille = [
        ("Banque en ligne A", base, 2200),
        ("Banque en ligne B", base + 0.10, 2400),
        ("Grande banque C", base + 0.30, 3000),
        ("Réseau mutualiste D", base + 0.40, 2800),
        ("Grande banque E", base + 0.50, 3200),
    ]
    return [{"banque": n, "taux": round(t, 2), "frais": f} for n, t, f in grille]


# ─── Actualités (démo, filtrées par profil) ──────────────────────────

_NEWS = [
    {
        "cat": "Taux/Crédit", "icon": "📉",
        "titre": "La BCE stabilise ses taux — impact sur les crédits immobiliers",
        "resume": "Les taux directeurs restent stables ce trimestre. Les taux de crédit "
                  "immobilier pourraient se détendre légèrement dans les prochains mois, "
                  "bon moment pour renégocier son assurance emprunteur.",
        "source": "Synthèse marché", "quand": "Il y a 2 h",
    },
    {
        "cat": "Immobilier", "icon": "🏠",
        "titre": "Prix immobiliers : reprise modérée dans les grandes métropoles",
        "resume": "Après deux ans de correction, les prix repartent doucement (+1 à 2 % sur "
                  "un an). Les acheteurs avec apport gardent un pouvoir de négociation.",
        "source": "Indice notaires", "quand": "Hier",
    },
    {
        "cat": "Investissement", "icon": "📈",
        "titre": "ETF Monde : les versements programmés séduisent les jeunes actifs",
        "resume": "Investir une somme fixe chaque mois sur un ETF diversifié lisse le risque "
                  "d'entrée. La régularité prime sur le timing de marché.",
        "source": "Éducation financière", "quand": "Il y a 1 j",
    },
    {
        "cat": "ESG", "icon": "🌱",
        "titre": "Labels ISR : comment repérer un fonds réellement responsable",
        "resume": "Tous les fonds 'verts' ne se valent pas. Vérifier le label ISR/Greenfin "
                  "et la composition réelle du portefeuille avant d'investir.",
        "source": "Guide ESG", "quand": "Il y a 2 j",
    },
    {
        "cat": "Économie", "icon": "💶",
        "titre": "Inflation sous contrôle : ce que ça change pour ton épargne",
        "resume": "Avec une inflation proche de 2 %, les livrets réglementés protègent mieux "
                  "le pouvoir d'achat qu'en 2023, mais restent insuffisants sur le long terme.",
        "source": "Analyse macro", "quand": "Il y a 3 j",
    },
    {
        "cat": "Crypto", "icon": "🪙",
        "titre": "Cryptoactifs : la part raisonnable dans un patrimoine diversifié",
        "resume": "Très volatils, les cryptoactifs sont à cantonner à une petite poche "
                  "(souvent < 5 %) que l'on peut accepter de voir fortement varier.",
        "source": "Prudence risque", "quand": "Il y a 4 j",
    },
]

CATEGORIES_NEWS = ["Tout", "Immobilier", "Taux/Crédit", "Investissement", "Économie", "ESG", "Crypto"]


def _pertinence(article: dict[str, Any], profile: dict[str, Any]) -> int:
    """Score de pertinence 1-10 selon le profil (immo, ESG, risque…)."""
    score = 5
    cat = article["cat"]
    projet = profile.get("projet_immo")
    if cat in ("Immobilier", "Taux/Crédit") and projet and projet != "Non":
        score += 3
    if cat == "ESG" and profile.get("esg"):
        score += 3
    if cat == "Investissement" and (profile.get("profil_risque", 5) >= 5):
        score += 2
    if cat == "Crypto" and (profile.get("profil_risque", 5) >= 8):
        score += 2
    if cat == "Crypto" and (profile.get("profil_risque", 5) < 4):
        score -= 2
    return max(1, min(10, score))


def get_news(profile: dict[str, Any], categorie: str = "Tout") -> list[dict[str, Any]]:
    """Actualités filtrées et triées par pertinence pour l'utilisateur."""
    items = []
    for a in _NEWS:
        if categorie != "Tout" and a["cat"] != categorie:
            continue
        art = dict(a)
        art["pertinence"] = _pertinence(a, profile)
        items.append(art)
    return sorted(items, key=lambda x: x["pertinence"], reverse=True)
