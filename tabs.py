"""Les 7 onglets de MINDVEST.

Chaque fonction show_* rend un onglet dans la zone principale. Les données
viennent de st.session_state.profile ; les modifications sont persistées via db.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import chatbot, db, finance, market_data
from .theme import (
    CHART_COLORS, ERROR_RED, GOLD, LIGHT_GOLD, PRIMARY_BLUE, SUCCESS_GREEN,
    TEXT_SECONDARY, WARNING_ORANGE, eur, info_box, kpi_card, page_header, progress_bar,
)

# ═══════════════════════════════════════════════════════════════════
#  Helpers graphiques
# ═══════════════════════════════════════════════════════════════════

def _plotly_layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#2C3E50", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def _save(profile: dict) -> None:
    db.save_profile(st.session_state.email, profile)


# ═══════════════════════════════════════════════════════════════════
#  Onglet 1 — Profil
# ═══════════════════════════════════════════════════════════════════

def show_profil(p: dict) -> None:
    page_header("👤", f"{p.get('name') or 'Ton profil'}",
                f"{p.get('age', '—')} ans · {p.get('email', '')}")

    marge = finance.marge_mensuelle(p)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("💰", "Salaire net", eur(p.get("salaire_net") or 0)), unsafe_allow_html=True)
    c2.markdown(kpi_card("🏠", "Charges fixes", eur(p.get("charges_fixes") or 0)), unsafe_allow_html=True)
    c3.markdown(kpi_card("✅", "Marge dispo", eur(marge) + " /mois"), unsafe_allow_html=True)
    c4.markdown(kpi_card("📊", "Profil risque",
                         f"{finance.risk_label(p.get('profil_risque', 5))} ({p.get('profil_risque', 5)}/10)"),
                unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 🎯 Objectifs par horizon")
    oc1, oc2, oc3 = st.columns(3)
    for col, titre, key in [
        (oc1, "1 an", "objectifs_1an"), (oc2, "5 ans", "objectifs_5ans"),
        (oc3, "10 ans +", "objectifs_10ans"),
    ]:
        with col:
            st.markdown(f"**{titre}**")
            items = p.get(key) or []
            if items:
                for o in items:
                    st.markdown(f"✅ {o}")
            else:
                st.caption("Aucun objectif renseigné")

    st.write("")
    with st.expander("✏️ Éditer mon profil"):
        with st.form("edit_profile"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Prénom & nom", value=p.get("name") or "")
                age = st.number_input("Âge", 18, 99, value=int(p.get("age") or 30))
                salaire = st.number_input("Salaire net (€)", 0, step=100,
                                          value=int(p.get("salaire_net") or 0))
                charges = st.number_input("Charges fixes (€)", 0, step=50,
                                          value=int(p.get("charges_fixes") or 0))
            with col2:
                risque = st.slider("Profil de risque", 0, 10, int(p.get("profil_risque", 5)))
                esg = st.checkbox("Préférence ESG", value=bool(p.get("esg")))
                situations = ["Locataire", "Propriétaire", "Hébergé(e)"]
                situ = st.selectbox("Situation immobilière", situations,
                                    index=situations.index(p["situation_immo"])
                                    if p.get("situation_immo") in situations else 0)
                projets = ["Non", "5+ ans", "2-5 ans", "<2 ans"]
                projet = st.selectbox("Projet immobilier", projets,
                                      index=projets.index(p["projet_immo"])
                                      if p.get("projet_immo") in projets else 0)
                budget = st.number_input("Budget immobilier (€)", 0, step=10000,
                                         value=int(p.get("budget_immo") or 0))
            if st.form_submit_button("💾 Enregistrer", type="primary"):
                p.update({
                    "name": name or None, "age": age, "salaire_net": salaire,
                    "charges_fixes": charges, "profil_risque": risque, "esg": esg,
                    "situation_immo": situ, "projet_immo": projet,
                    "budget_immo": budget or None,
                })
                _save(p)
                st.success("Profil mis à jour ✅")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  Onglet 2 — Patrimoine
# ═══════════════════════════════════════════════════════════════════

def show_patrimoine(p: dict) -> None:
    page_header("📊", "Mon patrimoine", "Vue d'ensemble et répartition de tes actifs")

    assets = p.get("patrimoine", [])
    total = finance.patrimoine_total(assets)
    score = finance.diversification_score(assets)
    rendement = finance.rendement_moyen_pondere(assets)

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_card("💎", "Patrimoine total", eur(total)), unsafe_allow_html=True)
    c2.markdown(kpi_card("📈", "Rendement moyen", f"{rendement:+.1f} %/an"), unsafe_allow_html=True)
    c3.markdown(kpi_card("🎯", "Diversification", f"{score}/100"), unsafe_allow_html=True)

    st.write("")
    st.markdown("#### ✏️ Détail de tes actifs")
    st.caption("Ajoute, modifie ou supprime des lignes, puis enregistre.")

    if assets:
        df = pd.DataFrame(assets)
    else:
        df = pd.DataFrame(columns=["categorie", "montant", "perf"])
    df = df.reindex(columns=["categorie", "montant", "perf"])

    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key="patri_editor",
        column_config={
            "categorie": st.column_config.SelectboxColumn(
                "Actif", options=finance.CATEGORIES, required=True),
            "montant": st.column_config.NumberColumn("Montant (€)", min_value=0, step=500, format="%d"),
            "perf": st.column_config.NumberColumn("Perf/an (%)", step=0.1, format="%.1f"),
        },
    )

    col_save, col_import = st.columns([1, 3])
    with col_save:
        if st.button("💾 Enregistrer", type="primary", use_container_width=True):
            cleaned = []
            for _, row in edited.iterrows():
                if pd.notna(row.get("categorie")) and (row.get("montant") or 0) > 0:
                    cleaned.append({
                        "categorie": row["categorie"],
                        "montant": float(row["montant"] or 0),
                        "perf": float(row["perf"] or 0),
                    })
            p["patrimoine"] = cleaned
            _save(p)
            st.success("Patrimoine enregistré ✅")
            st.rerun()

    if not assets:
        info_box("Renseigne tes actifs (immobilier, PEA, livrets…) pour débloquer "
                 "les graphiques et une stratégie personnalisée.", icon="ℹ️")
        return

    # Camembert de répartition
    rep = finance.repartition(assets)
    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### Répartition")
        fig = go.Figure(data=[go.Pie(
            labels=list(rep.keys()), values=list(rep.values()), hole=0.0,
            marker=dict(colors=CHART_COLORS), textinfo="label+percent",
            hovertemplate="%{label}<br>%{value:,.0f} €<br>%{percent}<extra></extra>",
        )])
        st.plotly_chart(_plotly_layout(fig), use_container_width=True)

    # Projection 10 ans
    with g2:
        st.markdown("#### Projection 10 ans")
        proj = finance.projection(p, annees=10)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=proj["annees"], y=proj["total"], mode="lines", name="Patrimoine total",
            line=dict(color=PRIMARY_BLUE, width=3), fill="tozeroy",
            fillcolor="rgba(15,76,139,0.10)",
            hovertemplate="Année %{x}<br>%{y:,.0f} €<extra></extra>",
        ))
        fig2.update_xaxes(title="Années")
        st.plotly_chart(_plotly_layout(fig2), use_container_width=True)
        final = proj["total"][-1]
        gain = final - total
        st.caption(f"Projection indicative : **{eur(final)}** dans 10 ans "
                   f"(+{eur(gain)}), hypothèses simplifiées.")


# ═══════════════════════════════════════════════════════════════════
#  Onglet 3 — Stratégie
# ═══════════════════════════════════════════════════════════════════

def show_strategie(p: dict) -> None:
    page_header("🎯", "Ta stratégie personnalisée",
                f"Âge {p.get('age','—')} · Profil {finance.risk_label(p.get('profil_risque',5))} · "
                f"ESG : {'Oui' if p.get('esg') else 'Non'}")

    if not p.get("salaire_net"):
        info_box("Complète ta situation financière dans l'onglet Profil pour générer ta stratégie.")
        return

    strat = finance.strategie(p)

    # Étape 1 — précaution
    prec = strat["precaution"]
    d = prec["diag"]
    st.markdown(
        f"""<div class="mv-step {prec['statut']}">
        <h3>Étape 1 · {prec['titre']}</h3>
        <span class="mv-badge {prec['statut']}">{prec['badge']}</span>
        {progress_bar(d['pct'])}
        Cible (3 mois de charges) : <b>{eur(d['cible'])}</b> · Actuel : <b>{eur(d['actuel'])}</b>
        · Manque : <b>{eur(d['manque'])}</b></div>""",
        unsafe_allow_html=True,
    )
    if d["manque"] > 0:
        info_box(f"En épargnant 200 €/mois, précaution complète en ~{d['mois_pour_completer']} mois.")

    # Étape 2 — immobilier
    if strat["immo"]:
        im = strat["immo"]
        st.markdown(
            f"""<div class="mv-step {im['statut']}">
            <h3>Étape 2 · {im['titre']}</h3>
            <span class="mv-badge {im['statut']}">{im['badge']} · horizon {im['horizon']}</span>
            {progress_bar(im['pct'])}
            Budget visé : <b>{eur(im['budget'])}</b> · Apport recommandé (20 %) : <b>{eur(im['apport_cible'])}</b>
            · Reste à épargner : <b>{eur(im['manque'])}</b></div>""",
            unsafe_allow_html=True,
        )

    # Étape 3 — structure d'investissement
    inv = strat["invest"]
    esg_txt = " · biais ESG activé 🌱" if inv["esg"] else ""
    st.markdown(
        f"""<div class="mv-step {inv['statut']}">
        <h3>Étape 3 · {inv['titre']}</h3>
        <span class="mv-badge {inv['statut']}">{inv['badge']}</span>
        Allocation cible ({inv['risk_label']}) : <b>{inv['actions_pct']}% actions</b> /
        <b>{inv['obligations_pct']}% obligations & fonds euros</b>{esg_txt}<br>
        <span style="color:{TEXT_SECONDARY};font-size:13px;">Enveloppes à privilégier : PEA
        (actions, fiscalité après 5 ans) et assurance-vie (flexibilité, fonds euros).</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # Étape 4 — répartition mensuelle
    alloc = strat["alloc"]["allocation"]
    st.markdown(f"""<div class="mv-step ok"><h3>Étape 4 · Répartition mensuelle</h3>
        Marge disponible : <b>{eur(strat['marge'])}</b> / mois</div>""",
        unsafe_allow_html=True)
    if alloc:
        cols = st.columns(len(alloc))
        for col, (label, val) in zip(cols, alloc.items()):
            col.markdown(kpi_card("→", label, eur(val)), unsafe_allow_html=True)

    # Projection
    st.write("")
    st.markdown("#### 📈 Projection 10 ans (si tu suis ce plan)")
    proj = finance.projection(p, annees=10)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=proj["annees"], y=proj["immobilier"], name="Immobilier",
                             stackgroup="one", line=dict(color=GOLD, width=0)))
    fig.add_trace(go.Scatter(x=proj["annees"], y=proj["financier"], name="Investissements",
                             stackgroup="one", line=dict(color=PRIMARY_BLUE, width=0)))
    fig.update_xaxes(title="Années")
    st.plotly_chart(_plotly_layout(fig), use_container_width=True)
    info_box("Projection sur hypothèses de rendement (actions/obligations selon ton profil, "
             "immobilier +3,5 %/an). Résultats non garantis.", icon="⚠️")


# ═══════════════════════════════════════════════════════════════════
#  Onglet 4 — Épargne vs Investissement
# ═══════════════════════════════════════════════════════════════════

def show_epargne(p: dict) -> None:
    page_header("💰", "Épargne vs Investissement", "Diagnostic et simulateurs personnalisés")
    rates = market_data.get_rates()
    t_diag, t_credit = st.tabs(["📊 Diagnostic épargne", "🏦 Crédit vs comptant"])

    # ── Diagnostic épargne de précaution ──
    with t_diag:
        charges = p.get("charges_fixes") or 0
        precaution_defaut = finance.epargne_precaution_actuelle(p.get("patrimoine", []))
        actuel = st.slider("Épargne d'urgence disponible aujourd'hui (€)", 0, 50000,
                           int(precaution_defaut), step=500)
        mensuel = st.slider("Combien peux-tu épargner par mois ? (€)", 0, 2000, 200, step=50)
        diag = finance.diagnostic_precaution(actuel, charges, max(mensuel, 1))
        badge = {"critique": ("neg", "🔴 Critique"), "en_cours": ("neg", "⚠️ À compléter"),
                 "ok": ("pos", "✅ Constituée"), "inconnu": ("neg", "Renseigne tes charges")}[diag["statut"]]
        st.markdown(
            f"""<div class="mv-scenario {badge[0]}">
            <span class="mv-badge {'ok' if badge[0]=='pos' else 'crit'}">{badge[1]}</span>
            <div class="mv-line"><span>Épargne actuelle</span><span>{eur(diag['actuel'])}</span></div>
            <div class="mv-line"><span>Objectif (3 mois de charges)</span><span>{eur(diag['cible'])}</span></div>
            <div class="mv-line"><span>Manque</span><span class="v-neg">{eur(diag['manque'])}</span></div>
            <div class="mv-line total"><span>Délai pour compléter</span>
            <span>{diag['mois_pour_completer']} mois</span></div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown("#### 🏆 Meilleurs placements pour la précaution")
        for l in market_data.livrets(rates):
            gain = 10000 * l["taux"] / 100
            st.markdown(
                f"""<div class="mv-info">{l['medaille']} <b>{l['nom']}</b> — <b>{l['taux']:.2f} %</b>
                · {l['avantages']}<br><span style="color:{TEXT_SECONDARY};font-size:12px;">
                Sur 10 000 € : ~{eur(gain)}/an · {l['inconvenients']}</span></div>""",
                unsafe_allow_html=True,
            )

    # ── Crédit vs comptant ──
    with t_credit:
        default_budget = int(p.get("budget_immo") or 250000)
        c1, c2 = st.columns(2)
        with c1:
            prix = st.slider("Prix du bien (€)", 100000, 800000, default_budget, step=10000)
            apport = st.slider("Apport disponible (€)", 0, 300000,
                               int(default_budget * 0.2), step=5000)
        with c2:
            duree = st.slider("Durée du crédit (ans)", 10, 30, 20)
            taux = st.slider("Taux du crédit (%)", 1.0, 6.0, float(rates["credit_immo_20ans"]), step=0.05)

        sim = finance.simulation_credit(prix, apport, taux / 100, duree)
        endettement = finance.taux_endettement(sim["mensualite_totale"], p.get("salaire_net") or 0)

        st.markdown(
            f"""<div class="mv-scenario neg">
            <h4 style="margin:0 0 8px 0;color:{PRIMARY_BLUE};">📊 Scénario crédit</h4>
            <div class="mv-line"><span>Montant emprunté</span><span>{eur(sim['emprunt'])}</span></div>
            <div class="mv-line"><span>Mensualité (hors assurance)</span><span>{eur(sim['mensualite'])}</span></div>
            <div class="mv-line"><span>+ assurance emprunteur</span><span>{eur(sim['assurance_mensuelle'])}</span></div>
            <div class="mv-line"><span>Coût total des intérêts</span>
            <span class="v-neg">{eur(sim['cout_interets'])}</span></div>
            <div class="mv-line total"><span>Mensualité totale</span>
            <span>{eur(sim['mensualite_totale'])}</span></div></div>""",
            unsafe_allow_html=True,
        )
        if p.get("salaire_net"):
            if endettement > 35:
                st.error(f"⚠️ Taux d'endettement : **{endettement:.0f}%** — au-dessus du seuil "
                         f"prudentiel de 35 %. Augmente ton apport ou vise un budget plus bas.")
            else:
                st.success(f"✅ Taux d'endettement : **{endettement:.0f}%** — sous le seuil de 35 %.")
        info_box("Le crédit permet de conserver son épargne investie (effet de levier), mais coûte "
                 "des intérêts. La bonne décision dépend du taux, de ton horizon et de ta stabilité pro.")


# ═══════════════════════════════════════════════════════════════════
#  Onglet 5 — Comparateur de taux
# ═══════════════════════════════════════════════════════════════════

def show_taux(p: dict) -> None:
    rates = market_data.get_rates()
    page_header("📈", "Comparateur de taux",
                f"Mise à jour : {rates.get('updated_at')} · Source : {rates.get('source')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("🏦", "Taux BCE (dépôt)", f"{rates['taux_bce']:.2f} %"), unsafe_allow_html=True)
    c2.markdown(kpi_card("📉", "Inflation", f"{rates['inflation']:.1f} %"), unsafe_allow_html=True)
    c3.markdown(kpi_card("🏠", "Crédit immo 20 ans", f"{rates['credit_immo_20ans']:.2f} %"), unsafe_allow_html=True)
    c4.markdown(kpi_card("💳", "Meilleur livret", f"{rates['livret_boost']:.2f} %"), unsafe_allow_html=True)

    st.write("")
    t_livrets, t_credit = st.tabs(["💳 Livrets", "🏦 Crédit immobilier"])

    with t_livrets:
        st.markdown("#### Classement des livrets (sur 10 000 € placés)")
        rows = []
        for l in market_data.livrets(rates):
            rows.append({"": l["medaille"], "Livret": l["nom"], "Taux": f"{l['taux']:.2f} %",
                         "Gain 1 an": eur(10000 * l["taux"] / 100), "Avantages": l["avantages"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        info_box("Astuce : combiner LDDS (défiscalisé) et un livret boosté maximise le rendement "
                 "de la poche de précaution.")

    with t_credit:
        st.markdown("#### Grille de taux crédit immobilier (indicative)")
        prix = st.number_input("Montant emprunté (€)", 50000, 1000000,
                               int(p.get("budget_immo") or 250000) - int((p.get("budget_immo") or 250000) * 0.2),
                               step=10000)
        duree = st.slider("Durée (ans)", 10, 30, 20, key="taux_duree")
        rows = []
        for b in market_data.credit_banques(rates):
            m = finance.mensualite(prix, b["taux"] / 100, duree)
            rows.append({"Banque": b["banque"], "Taux": f"{b['taux']:.2f} %",
                         "Mensualité": eur(m), "Frais de dossier": eur(b["frais"])})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        banks = market_data.credit_banques(rates)
        ecart = (banks[-1]["taux"] - banks[0]["taux"]) / 100 * prix * duree
        info_box(f"Écart entre la meilleure et la moins bonne offre : ~{eur(ecart)} sur {duree} ans. "
                 f"Faire jouer la concurrence (ou un courtier) est très rentable.")


# ═══════════════════════════════════════════════════════════════════
#  Onglet 6 — Actualités
# ═══════════════════════════════════════════════════════════════════

def show_actualites(p: dict) -> None:
    page_header("📰", "Actualités filtrées pour toi",
                f"Profil {finance.risk_label(p.get('profil_risque',5))} · "
                f"ESG {'oui' if p.get('esg') else 'non'} · "
                f"Projet immo : {p.get('projet_immo') or '—'}")

    categorie = st.radio("Filtres", market_data.CATEGORIES_NEWS, horizontal=True,
                         label_visibility="collapsed")
    news = market_data.get_news(p, categorie)
    if not news:
        st.caption("Aucune actualité dans cette catégorie.")
        return

    for a in news:
        cls = "mv-news" if a["pertinence"] >= 8 else ("mv-news mid" if a["pertinence"] >= 5 else "mv-news low")
        st.markdown(
            f"""<div class="mv-card {cls}">
            <div class="title">{a['icon']} {a['titre']}</div>
            <div class="meta">{a['source']} · {a['quand']} · Pertinence {a['pertinence']}/10 · {a['cat']}</div>
            {a['resume']}</div>""",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════
#  Onglet 7 — Chatbot
# ═══════════════════════════════════════════════════════════════════

SUGGESTIONS = [
    "Faut-il que j'ouvre un PEA ou une assurance-vie ?",
    "Est-ce le bon moment pour un crédit immobilier ?",
    "Comment bien diversifier mon portefeuille ?",
    "Combien devrais-je garder en épargne de précaution ?",
    "Comment réduire mes impôts légalement ?",
    "Par où commencer pour investir avec ma marge ?",
]


def _bubble(role: str, content: str) -> str:
    cls = "mv-bubble-user" if role == "user" else "mv-bubble-bot"
    safe = content.replace("\n", "<br>")
    return f'<div class="{cls}">{safe}</div>'


def show_chatbot(p: dict) -> None:
    page_header("💬", "Chatbot finance", "Réponses personnalisées, basées sur ton profil réel")

    email = st.session_state.email
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = db.load_chat_history(email)

    configured = chatbot.is_configured()
    if not configured:
        info_box("Le chatbot nécessite une clé API Anthropic. Ajoute ANTHROPIC_API_KEY dans "
                 "<code>.streamlit/secrets.toml</code> (voir secrets.toml.example) puis relance l'app.",
                 icon="🔑")

    # Statut freemium
    used = db.count_messages_this_month(email)
    if p.get("plan") != "premium":
        restant = max(0, chatbot.FREE_MONTHLY_LIMIT - used)
        st.caption(f"Plan gratuit · **{restant}** message(s) restant(s) ce mois-ci "
                   f"(sur {chatbot.FREE_MONTHLY_LIMIT}).")

    # Historique
    for m in st.session_state.chat_history:
        st.markdown(_bubble(m["role"], m["content"]), unsafe_allow_html=True)

    # Suggestions rapides
    pending = None
    with st.expander("💡 Questions rapides", expanded=not st.session_state.chat_history):
        cols = st.columns(2)
        for i, q in enumerate(SUGGESTIONS):
            if cols[i % 2].button(q, key=f"sugg_{i}", use_container_width=True):
                pending = q

    # Outils historique
    if st.session_state.chat_history:
        if st.button("🗑️ Effacer l'historique"):
            db.clear_chat(email)
            st.session_state.chat_history = []
            st.rerun()

    prompt = st.chat_input("Pose ta question finance…", disabled=not configured)
    user_msg = prompt or pending
    if not user_msg:
        return

    # Garde-fou freemium
    if p.get("plan") != "premium" and used >= chatbot.FREE_MONTHLY_LIMIT:
        st.warning("⚠️ Limite du plan gratuit atteinte ce mois-ci. Passe en Premium pour un accès illimité.")
        return

    # Message utilisateur
    st.session_state.chat_history.append({"role": "user", "content": user_msg})
    db.add_chat_message(email, "user", user_msg)
    st.markdown(_bubble("user", user_msg), unsafe_allow_html=True)

    # Réponse en streaming
    rates = market_data.get_rates()
    try:
        with st.spinner("Claude réfléchit…"):
            full = st.write_stream(
                chatbot.stream_reply(st.session_state.chat_history, p, rates)
            )
    except Exception as exc:  # clé invalide, réseau, etc.
        full = f"⚠️ Impossible de contacter l'assistant ({type(exc).__name__}). Vérifie ta clé API."
        st.error(full)

    st.session_state.chat_history.append({"role": "assistant", "content": full})
    db.add_chat_message(email, "assistant", full)
    st.rerun()
