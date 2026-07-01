"""Chatbot finance MINDVEST — propulsé par Claude (API Anthropic).

Le modèle reçoit en contexte le profil réel de l'utilisateur et les taux du
moment, avec des règles de conformité strictes (pas de conseil personnalisé
direct, pédagogie + explication des mécanismes).
"""
from __future__ import annotations

import json
from typing import Any, Iterator

import streamlit as st

from . import finance

# Modèle Claude le plus capable à ce jour. Pour réduire les coûts sur un usage
# à fort volume, tu peux basculer sur "claude-haiku-4-5".
MODEL = "claude-opus-4-8"
MAX_TOKENS = 1500

# Limite du plan gratuit (messages utilisateur par mois).
FREE_MONTHLY_LIMIT = 5


def is_configured() -> bool:
    """Vrai si une clé API Anthropic est disponible dans les secrets."""
    try:
        return bool(st.secrets.get("ANTHROPIC_API_KEY"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _client():
    from anthropic import Anthropic
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def build_system_prompt(profile: dict[str, Any], rates: dict[str, Any]) -> str:
    marge = finance.marge_mensuelle(profile)
    actions, oblig = finance.allocation_cible(profile.get("profil_risque", 5))
    patrimoine = profile.get("patrimoine", [])
    contexte = {
        "prenom_nom": profile.get("name"),
        "age": profile.get("age"),
        "salaire_net_mensuel": profile.get("salaire_net"),
        "charges_fixes_mensuelles": profile.get("charges_fixes"),
        "marge_disponible_mensuelle": marge,
        "profil_risque_sur_10": profile.get("profil_risque"),
        "profil_risque_libelle": finance.risk_label(profile.get("profil_risque", 5)),
        "allocation_cible": f"{actions}% actions / {oblig}% obligations-fonds euros",
        "preference_esg": profile.get("esg"),
        "situation_immobiliere": profile.get("situation_immo"),
        "projet_immobilier": profile.get("projet_immo"),
        "budget_immobilier": profile.get("budget_immo"),
        "patrimoine": patrimoine,
        "patrimoine_total": finance.patrimoine_total(patrimoine),
    }
    taux = {
        "taux_bce": rates.get("taux_bce"),
        "inflation": rates.get("inflation"),
        "livret_a": rates.get("livret_a"),
        "meilleur_livret": rates.get("livret_boost"),
        "credit_immo_20ans": rates.get("credit_immo_20ans"),
        "prix_m2_france": rates.get("prix_m2_france"),
    }
    return f"""Tu es MINDVEST, un assistant patrimonial expert en finances \
personnelles françaises, spécialisé pour les jeunes actifs (20-45 ans).

CONTEXTE UTILISATEUR (chiffres réels, à utiliser dans tes réponses) :
{json.dumps(contexte, ensure_ascii=False, indent=2)}

TAUX ET DONNÉES DE MARCHÉ DU JOUR :
{json.dumps(taux, ensure_ascii=False, indent=2)}

RÈGLES :
1. Personnalise au maximum avec SES chiffres (marge, patrimoine, projet immo).
2. Cite des ordres de grandeur et fais des calculs concrets.
3. CONFORMITÉ : ne donne jamais de recommandation d'achat d'un produit précis \
("achète tel fonds"). Explique les mécanismes, les enveloppes (PEA, \
assurance-vie), les avantages/risques, et laisse l'utilisateur décider.
4. Pédagogie : réponses claires, structurées, sans jargon non expliqué.
5. Termine par 1 à 3 prochaines étapes actionnables.
6. Rappelle si pertinent que tu ne remplaces pas un conseiller agréé.
7. Réponds en français, ton chaleureux mais précis. Reste sous ~400 mots sauf \
demande explicite de détail."""


def stream_reply(messages: list[dict[str, str]], profile: dict[str, Any],
                 rates: dict[str, Any]) -> Iterator[str]:
    """Générateur des morceaux de texte de la réponse (pour st.write_stream)."""
    system = build_system_prompt(profile, rates)
    client = _client()
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
