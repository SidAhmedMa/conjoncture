"""Chargement de site.json et petits utilitaires de mise en forme."""

import json
import os
from pathlib import Path

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
MOIS_COURT = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


class Site:
    """Configuration du site, plus l'index des rubriques."""

    def __init__(self, data, root):
        self.root = Path(root)
        self.data = data
        self.base = (data.get("base") or "").rstrip("/")
        self.rubriques = [Rubrique(r, self) for r in data.get("rubriques", [])]
        self.by_slug = {r.slug: r for r in self.rubriques}

    def __getattr__(self, name):
        try:
            return self.data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def get(self, key, default=""):
        return self.data.get(key, default)

    def url(self, path):
        """Préfixe un chemin absolu du sous-répertoire de déploiement."""
        if path.startswith(("http://", "https://", "mailto:", "#")):
            return path
        return self.base + path if path.startswith("/") else path

    def absolute(self, path):
        if path.startswith(("http://", "https://")):
            return path
        return self.data.get("url", "").rstrip("/") + self.url(path)

    @classmethod
    def load(cls, root="."):
        """Charge site.json, puis applique les surcharges d'environnement.

        Un déploiement de relecture (GitHub Pages, préproduction) peut ainsi
        changer de domaine sans modifier site.json, qui reste la référence du
        site de production :

            TCR_URL      origine seule, sans chemin — https://exemple.github.io
            TCR_BASE     sous-répertoire de publication — /conjoncture
            TCR_NOINDEX  à 1, demande aux moteurs de ne pas indexer
        """
        root = Path(root)
        data = json.loads((root / "site.json").read_text(encoding="utf-8"))
        if os.environ.get("TCR_URL"):
            data["url"] = os.environ["TCR_URL"].rstrip("/")
        if os.environ.get("TCR_BASE"):
            data["base"] = "/" + os.environ["TCR_BASE"].strip("/")
        if os.environ.get("TCR_NOINDEX") == "1":
            data["noindex"] = True
        return cls(data, root)


class Rubrique:
    def __init__(self, data, site):
        self.data = data
        self.site = site
        self.slug = data["slug"]
        self.name = data["name"]
        self.keywords = data.get("keywords", "")
        self.description = data.get("description", "")
        self.accent = data.get("accent", "#1F4E8C")
        self.icon = data.get("icon", "insights")

    @property
    def url(self):
        return self.site.url(f"/{self.slug}/")


def fr_date(value, short=False):
    """30 juillet 2026 — ou « 30 juil. 2026 » en version courte."""
    if value is None:
        return ""
    names = MOIS_COURT if short else MOIS
    return f"{value.day} {names[value.month - 1]} {value.year}"


def iso_date(value):
    return value.isoformat() if value else ""
