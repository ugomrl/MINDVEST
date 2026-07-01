"""Design system MINDVEST : palette, typographie, CSS global et composants UI.

Source de vérité des couleurs. Les mêmes valeurs sont utilisées dans le bloc
CSS (littéral, pour éviter l'échappement des accolades) et dans les helpers
Python qui produisent du HTML inline.
"""
from __future__ import annotations

import streamlit as st

# ─── Palette officielle ──────────────────────────────────────────────
PRIMARY_BLUE = "#0F4C8B"
DARK_BLUE = "#0A2E52"
GOLD = "#D4A574"
LIGHT_GOLD = "#E8D4C4"
BG_LIGHT = "#F8F9FB"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#6B7280"
SUCCESS_GREEN = "#10B981"
WARNING_ORANGE = "#F97316"
ERROR_RED = "#EF4444"
BORDER = "#E5E7EB"

# Palette pour les graphiques Plotly (bleu, or, vert, orange, rouge, gris).
CHART_COLORS = [PRIMARY_BLUE, GOLD, SUCCESS_GREEN, WARNING_ORANGE, ERROR_RED, "#94A3B8"]


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp { background-color: #F8F9FB; }

/* Masquer le chrome Streamlit par défaut */
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Largeur de contenu confortable */
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1150px; }

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0A2E52;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #E5E7EB; }
[data-testid="stSidebar"] .stButton > button {
    background: #D4A574;
    color: #0A2E52;
    font-weight: 700;
    border: none;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #C9975F;
    color: #0A2E52;
}

.mv-logo {
    display: flex; align-items: center; gap: 10px;
    font-weight: 800; font-size: 22px; letter-spacing: 0.5px;
    color: #D4A574; margin: 4px 0 18px 0;
}
.mv-logo .spark { font-size: 24px; }

.mv-premium-card {
    background: linear-gradient(135deg, #0F4C8B 0%, #0A2E52 100%);
    border: 1px solid #D4A574; border-radius: 12px;
    padding: 16px; margin-top: 10px; text-align: center;
}
.mv-premium-card .title { color: #D4A574; font-weight: 700; font-size: 15px; }
.mv-premium-card .sub { color: #E5E7EB; font-size: 12px; margin-top: 4px; }

.mv-plan-pill {
    display:inline-block; padding: 4px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 600;
}
.mv-plan-free { background: rgba(212,165,116,0.15); color: #D4A574; border: 1px solid #D4A574; }
.mv-plan-premium { background: #D4A574; color: #0A2E52; }

/* ── Titres ──────────────────────────────────────────── */
.mv-h1 {
    font-size: 30px; font-weight: 800; color: #0F4C8B;
    letter-spacing: -0.5px; margin: 0 0 4px 0;
}
.mv-sub { color: #6B7280; font-size: 14px; margin-bottom: 20px; }
.mv-h2 { font-size: 20px; font-weight: 700; color: #0F4C8B; margin: 8px 0 12px 0; }

/* ── Cartes ──────────────────────────────────────────── */
.mv-card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    padding: 20px; margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.mv-header-card {
    background: linear-gradient(135deg, #0F4C8B 0%, #0A2E52 100%);
    border-radius: 14px; padding: 22px 24px; margin-bottom: 22px;
    color: #FFFFFF; box-shadow: 0 10px 25px rgba(15,76,139,0.15);
}
.mv-header-card h1 { color: #FFFFFF; font-size: 24px; font-weight: 800; margin: 0; }
.mv-header-card p { color: #E8D4C4; font-size: 13px; margin: 6px 0 0 0; }

.mv-kpi {
    background: linear-gradient(135deg, #F8F9FB 0%, #FFFFFF 100%);
    border: 1px solid #E5E7EB; border-left: 4px solid #D4A574;
    border-radius: 10px; padding: 16px; height: 100%;
}
.mv-kpi .icon { font-size: 24px; }
.mv-kpi .label { color: #6B7280; font-size: 12px; font-weight: 500; margin-top: 4px; }
.mv-kpi .value { color: #0F4C8B; font-size: 22px; font-weight: 800; line-height: 1.1; }

/* ── Étapes stratégie ────────────────────────────────── */
.mv-step {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 4px solid #0F4C8B;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.mv-step.crit { border-left-color: #EF4444; }
.mv-step.warn { border-left-color: #F97316; }
.mv-step.ok   { border-left-color: #10B981; }
.mv-step.soon { border-left-color: #0F4C8B; }
.mv-step h3 { font-size: 16px; font-weight: 700; color: #0A2E52; margin: 0 0 6px 0; }

.mv-badge {
    display:inline-block; padding: 4px 10px; border-radius: 6px;
    font-size: 12px; font-weight: 600; margin-right: 6px;
}
.mv-badge.crit { background: rgba(239,68,68,0.12); color: #EF4444; }
.mv-badge.warn { background: rgba(249,115,22,0.12); color: #F97316; }
.mv-badge.ok   { background: rgba(16,185,129,0.12); color: #10B981; }
.mv-badge.soon { background: rgba(15,76,139,0.12); color: #0F4C8B; }
.mv-badge.gold { background: #E8D4C4; color: #0F4C8B; }

/* ── Barre de progression maison ─────────────────────── */
.mv-progress { background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden; margin: 8px 0; }
.mv-progress > span {
    display:block; height: 100%;
    background: linear-gradient(90deg, #0F4C8B 0%, #D4A574 100%);
}

/* ── Cartes scénario / résultat ──────────────────────── */
.mv-scenario {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FB 100%);
    border: 1px solid #E5E7EB; border-radius: 12px; padding: 18px;
    margin: 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.mv-scenario.pos { border-left: 4px solid #10B981; }
.mv-scenario.neg { border-left: 4px solid #EF4444; }
.mv-line { display:flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #EEF1F5; font-size: 14px; }
.mv-line .v-pos { color: #10B981; font-weight: 600; }
.mv-line .v-neg { color: #EF4444; font-weight: 600; }
.mv-line.total { background: rgba(15,76,139,0.06); border-radius: 6px; padding: 10px 8px; border: none; font-weight: 800; color: #0F4C8B; margin-top: 6px; }

/* ── Info / actu ─────────────────────────────────────── */
.mv-info {
    background: linear-gradient(90deg, rgba(15,76,139,0.05) 0%, rgba(212,165,116,0.06) 100%);
    border: 1px solid #D4A574; border-left: 4px solid #D4A574;
    border-radius: 8px; padding: 12px 14px; font-size: 13px; color: #2C3E50;
    margin: 10px 0;
}
.mv-news { border-left: 4px solid #10B981; }
.mv-news.mid { border-left-color: #F97316; }
.mv-news.low { border-left-color: #9CA3AF; }
.mv-news .title { font-weight: 700; color: #0F4C8B; font-size: 15px; }
.mv-news .meta { color: #6B7280; font-size: 12px; margin: 4px 0 8px 0; }

/* ── Chat ────────────────────────────────────────────── */
.mv-bubble-user {
    background: #0F4C8B; color: #FFFFFF; border-radius: 16px 16px 4px 16px;
    padding: 12px 16px; margin: 8px 0 8px auto; max-width: 78%;
    width: fit-content; font-size: 14px; line-height: 1.55;
}
.mv-bubble-bot {
    background: #FFFFFF; color: #2C3E50; border: 1px solid #E5E7EB;
    border-radius: 16px 16px 16px 4px; padding: 12px 16px; margin: 8px auto 8px 0;
    max-width: 82%; width: fit-content; font-size: 14px; line-height: 1.6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.mv-bubble-bot p { margin: 0 0 8px 0; }
.mv-bubble-bot p:last-child { margin-bottom: 0; }

/* ── Boutons Streamlit ───────────────────────────────── */
.stButton > button {
    border-radius: 8px; font-weight: 600; border: 1px solid #E5E7EB;
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background: #0F4C8B; border: none; color: #FFFFFF;
}
.stButton > button[kind="primary"]:hover {
    background: #0A2E52; box-shadow: 0 8px 18px rgba(15,76,139,0.18);
    transform: translateY(-1px);
}

/* Inputs */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    border-radius: 8px !important;
}

/* Metric natif */
[data-testid="stMetricValue"] { color: #0F4C8B; font-weight: 800; }
</style>
"""


def inject_css() -> None:
    """Injecte le CSS global (à appeler une fois, tôt dans app.py)."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ─── Helpers de composants (retournent/insèrent du HTML) ─────────────

def page_header(icon: str, title: str, subtitle: str = "") -> None:
    """En-tête bleu dégradé en haut d'un onglet."""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="mv-header-card"><h1>{icon} {title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(icon: str, label: str, value: str) -> str:
    return (
        f'<div class="mv-kpi"><div class="icon">{icon}</div>'
        f'<div class="value">{value}</div><div class="label">{label}</div></div>'
    )


def progress_bar(pct: float) -> str:
    pct = max(0.0, min(100.0, pct))
    return f'<div class="mv-progress"><span style="width:{pct:.0f}%"></span></div>'


def info_box(text: str, icon: str = "💡") -> None:
    st.markdown(f'<div class="mv-info">{icon} {text}</div>', unsafe_allow_html=True)


def eur(value: float) -> str:
    """Formate un montant en euros à la française : 12 500 €."""
    try:
        return f"{value:,.0f} €".replace(",", " ")
    except (ValueError, TypeError):
        return "— €"
