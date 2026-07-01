"""Authentification MINDVEST — connexion par email (profil lié au mail).

Version MVP : saisie d'email (pas de mot de passe), qui crée ou recharge le
profil. Le "magic link" par email (Brevo/Mailgun) et Google OAuth sont des
évolutions prévues — voir README. L'email sert d'identifiant du profil.
"""
from __future__ import annotations

import re

import streamlit as st

from . import db
from .theme import PRIMARY_BLUE, TEXT_SECONDARY

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def current_email() -> str | None:
    return st.session_state.get("email")


def login(email: str) -> None:
    """Ouvre la session pour cet email (crée le profil si nécessaire)."""
    email = email.strip().lower()
    profile = db.get_user(email) or db.create_user(email)
    st.session_state.email = email
    st.session_state.profile = profile


def logout() -> None:
    for key in ("email", "profile", "chat_history", "onboard_step", "nav"):
        st.session_state.pop(key, None)


def show_login() -> None:
    """Écran de connexion plein écran."""
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:6vh;">
          <div style="font-size:52px;">🧠💎</div>
          <div style="font-size:34px; font-weight:800; color:{PRIMARY_BLUE};
                      letter-spacing:2px;">MINDVEST</div>
          <div style="color:{TEXT_SECONDARY}; font-size:16px; margin-top:8px;">
            Ton assistant patrimonial intelligent
          </div>
          <div style="color:{TEXT_SECONDARY}; font-size:14px;">
            Gère ton patrimoine comme un expert
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        with st.container(border=True):
            st.markdown("#### Connecte-toi avec ton email")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "Email", placeholder="tape ton email…",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button(
                    "Continuer  →", type="primary", use_container_width=True
                )
            if submitted:
                if is_valid_email(email):
                    login(email)
                    st.rerun()
                else:
                    st.error("❌ Merci d'entrer une adresse email valide.")
            st.caption(
                "En continuant, tu acceptes que ton profil soit enregistré "
                "localement et lié à cet email. Aucune donnée n'est partagée."
            )

    st.markdown(
        f"<div style='text-align:center; color:{TEXT_SECONDARY}; font-size:12px; "
        f"margin-top:24px;'>© 2026 MINDVEST · Confidentialité · Conditions d'usage</div>",
        unsafe_allow_html=True,
    )
