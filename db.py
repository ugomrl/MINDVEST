"""Persistance SQLite pour MINDVEST.

Un utilisateur = une ligne (identifiée par son email). Le profil complet
(patrimoine inclus) est stocké en JSON pour rester flexible. L'historique de
chat et les notes sont dans des tables séparées.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "mindvest.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crée les tables si elles n'existent pas. Idempotent."""
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT,
                profile_json TEXT,
                created_at TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                stars INTEGER,
                created_at TEXT
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Utilisateurs / profils ──────────────────────────────────────────

def default_profile() -> dict[str, Any]:
    """Profil vierge — placeholders, pas de valeurs par défaut trompeuses."""
    return {
        "name": None,
        "age": None,
        "salaire_net": None,
        "charges_fixes": None,
        "dettes": None,
        "objectifs_1an": [],
        "objectifs_5ans": [],
        "objectifs_10ans": [],
        "profil_risque": 5,          # score 0-10
        "esg": False,
        "situation_immo": None,       # Locataire / Propriétaire / Hébergé(e)
        "projet_immo": None,          # Non / 5+ ans / 2-5 ans / <2 ans
        "budget_immo": None,
        "patrimoine": [],             # liste de {categorie, montant, perf}
        "plan": "gratuit",            # gratuit | premium
        "premium_until": None,
        "onboarded": False,
        "created_at": None,
    }


def get_user(email: str) -> dict[str, Any] | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    profile = default_profile()
    profile.update(json.loads(row["profile_json"] or "{}"))
    profile["name"] = row["name"]
    profile["created_at"] = row["created_at"]
    profile["email"] = email
    return profile


def create_user(email: str) -> dict[str, Any]:
    """Crée un utilisateur vide (au premier login) et retourne son profil."""
    existing = get_user(email)
    if existing:
        return existing
    profile = default_profile()
    created = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO users (email, name, profile_json, created_at) VALUES (?,?,?,?)",
            (email, None, json.dumps(profile), created),
        )
    profile["created_at"] = created
    profile["email"] = email
    return profile


def save_profile(email: str, profile: dict[str, Any]) -> None:
    """Écrase le profil complet de l'utilisateur."""
    to_store = {k: v for k, v in profile.items() if k not in ("email", "created_at")}
    with _conn() as c:
        c.execute(
            "UPDATE users SET name = ?, profile_json = ? WHERE email = ?",
            (profile.get("name"), json.dumps(to_store), email),
        )


# ─── Chat ────────────────────────────────────────────────────────────

def add_chat_message(email: str, role: str, content: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO chat_messages (email, role, content, created_at) VALUES (?,?,?,?)",
            (email, role, content, _now()),
        )


def load_chat_history(email: str, limit: int = 100) -> list[dict[str, str]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM chat_messages WHERE email = ? "
            "ORDER BY id ASC LIMIT ?",
            (email, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def clear_chat(email: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM chat_messages WHERE email = ?", (email,))


def count_messages_this_month(email: str) -> int:
    """Nombre de messages 'user' envoyés depuis le début du mois courant."""
    start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM chat_messages "
            "WHERE email = ? AND role = 'user' AND created_at >= ?",
            (email, start),
        ).fetchone()
    return int(row["n"])


def save_rating(email: str, stars: int) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO ratings (email, stars, created_at) VALUES (?,?,?)",
            (email, stars, _now()),
        )
