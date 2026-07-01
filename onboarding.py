"""Parcours d'onboarding MINDVEST en 5 étapes.

Le profil de travail vit dans st.session_state.profile ; il est persisté en
base à chaque étape validée et marqué 'onboarded' à la fin.
"""
from __future__ import annotations

import streamlit as st

from . import db, finance
from .theme import GOLD, PRIMARY_BLUE, progress_bar, eur

TOTAL_STEPS = 5

OBJECTIFS_1AN = ["Épargne de précaution", "Commencer à investir", "Rembourser une dette", "Rien de particulier"]
OBJECTIFS_5ANS = ["Acheter un bien immobilier", "Portefeuille investi", "Diminuer mes dettes", "Préparer ma retraite"]
OBJECTIFS_10ANS = ["Retraite confortable", "Patrimoine diversifié", "Placements ESG", "Indépendance financière"]


def _step() -> int:
    return st.session_state.get("onboard_step", 1)


def _goto(step: int) -> None:
    st.session_state.onboard_step = max(1, min(TOTAL_STEPS, step))
    db.save_profile(st.session_state.email, st.session_state.profile)
    st.rerun()


def _nav(can_finish: bool = False) -> None:
    """Boutons Précédent / Suivant (ou Terminer)."""
    step = _step()
    left, right = st.columns(2)
    with left:
        if step > 1:
            if st.button("◀ Précédent", use_container_width=True):
                _goto(step - 1)
    with right:
        if can_finish:
            if st.button("Terminer  ✓", type="primary", use_container_width=True):
                st.session_state.profile["onboarded"] = True
                db.save_profile(st.session_state.email, st.session_state.profile)
                st.session_state.nav = "Profil"
                st.rerun()
        else:
            if st.button("Suivant  ▶", type="primary", use_container_width=True):
                _goto(step + 1)


def run() -> None:
    """Affiche l'étape courante de l'onboarding."""
    p = st.session_state.profile
    step = _step()

    st.markdown(
        f"<div style='font-size:26px;font-weight:800;color:{PRIMARY_BLUE};'>"
        f"Bienvenue sur MINDVEST 🧠💎</div>", unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='color:{GOLD};font-weight:600;'>Étape {step}/{TOTAL_STEPS}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(progress_bar(step / TOTAL_STEPS * 100), unsafe_allow_html=True)
    st.write("")

    with st.container(border=True):
        if step == 1:
            _step1(p)
        elif step == 2:
            _step2(p)
        elif step == 3:
            _step3(p)
        elif step == 4:
            _step4(p)
        else:
            _step5(p)

    _nav(can_finish=(step == TOTAL_STEPS))


def _step1(p: dict) -> None:
    st.markdown("### Qui es-tu ?")
    p["name"] = st.text_input(
        "Prénom & nom", value=p.get("name") or "",
        placeholder="tape ton nom complet…") or None
    p["age"] = st.slider("Âge", 18, 70, value=int(p.get("age") or 30))


def _step2(p: dict) -> None:
    st.markdown("### Ta situation financière")
    p["salaire_net"] = st.number_input(
        "💰 Salaire NET mensuel (€)", min_value=0, step=100,
        value=int(p.get("salaire_net") or 0))
    p["charges_fixes"] = st.number_input(
        "🏠 Charges fixes mensuelles (loyer, abonnements…) (€)", min_value=0, step=50,
        value=int(p.get("charges_fixes") or 0))
    p["dettes"] = st.number_input(
        "📊 Dettes / crédits en cours (€, 0 si aucune)", min_value=0, step=100,
        value=int(p.get("dettes") or 0))
    marge = finance.marge_mensuelle(p)
    if marge > 0:
        st.success(f"✅ Marge disponible estimée : **{eur(marge)} / mois**")


def _step3(p: dict) -> None:
    st.markdown("### Tes objectifs")
    st.markdown("**🎯 Dans 1 an**")
    p["objectifs_1an"] = st.multiselect(
        "Objectifs 1 an", OBJECTIFS_1AN, default=p.get("objectifs_1an") or [],
        label_visibility="collapsed")
    st.markdown("**🎯 Dans 5 ans**")
    p["objectifs_5ans"] = st.multiselect(
        "Objectifs 5 ans", OBJECTIFS_5ANS, default=p.get("objectifs_5ans") or [],
        label_visibility="collapsed")
    st.markdown("**🎯 Dans 10 ans et +**")
    p["objectifs_10ans"] = st.multiselect(
        "Objectifs 10 ans", OBJECTIFS_10ANS, default=p.get("objectifs_10ans") or [],
        label_visibility="collapsed")


def _step4(p: dict) -> None:
    st.markdown("### Ton appétence au risque")
    p["profil_risque"] = st.slider(
        "De très prudent (0) à offensif (10)", 0, 10,
        value=int(p.get("profil_risque", 5)))
    actions, oblig = finance.allocation_cible(p["profil_risque"])
    st.markdown(
        f"Profil : **{finance.risk_label(p['profil_risque'])}** · "
        f"Allocation cible indicative : **{actions}% actions / {oblig}% obligations & fonds euros**")
    p["esg"] = st.checkbox(
        "🌱 Prioriser les investissements responsables (ESG)",
        value=bool(p.get("esg")))


def _step5(p: dict) -> None:
    st.markdown("### Situation immobilière")
    situations = ["Locataire", "Propriétaire", "Hébergé(e)"]
    p["situation_immo"] = st.radio(
        "🏠 Es-tu propriétaire ou locataire ?", situations,
        index=situations.index(p["situation_immo"]) if p.get("situation_immo") in situations else 0)

    projets = ["Non", "5+ ans", "2-5 ans", "<2 ans"]
    p["projet_immo"] = st.radio(
        "🎯 Projet d'achat immobilier ?", projets,
        index=projets.index(p["projet_immo"]) if p.get("projet_immo") in projets else 0,
        help="'<2 ans' = très bientôt")

    if p["projet_immo"] != "Non":
        p["budget_immo"] = st.number_input(
            "💰 Budget estimé pour l'achat (€)", min_value=0, step=10000,
            value=int(p.get("budget_immo") or 0))
    else:
        p["budget_immo"] = None
