"""Lecture de l'en-tête `---` placé en tête des fichiers Markdown.

Sous-ensemble volontairement réduit de YAML : `cle: valeur`, listes en ligne
`[a, b]` ou à puces, booléens, entiers, flottants et dates ISO (AAAA-MM-JJ).
"""

import datetime
import re

_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
_ITEM = re.compile(r"^\s*-\s+(.*)$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT = re.compile(r"^-?\d+$")
_FLOAT = re.compile(r"^-?\d+\.\d+$")


def split(text):
    """Retourne (metadonnees, corps) pour un document `---` ... `---`."""
    text = text.replace("\r\n", "\n").lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    return parse("\n".join(lines[1:end])), "\n".join(lines[end + 1 :]).lstrip("\n")


def parse(block):
    meta, key = {}, None
    for raw in block.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = _ITEM.match(raw)
        if item and key is not None:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(coerce(item.group(1)))
            continue
        found = _KEY.match(raw)
        if not found:
            continue
        key, rest = found.group(1), found.group(2).strip()
        meta[key] = [] if rest == "" else coerce(rest)
    return meta


def coerce(value):
    """Convertit une valeur textuelle en type Python."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [coerce(part) for part in _split_commas(inner)] if inner else []
    low = value.lower()
    if low in ("true", "yes", "oui"):
        return True
    if low in ("false", "no", "non"):
        return False
    if low in ("null", "none", "~"):
        return None
    if _DATE.match(value):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return value
    if _INT.match(value):
        return int(value)
    if _FLOAT.match(value):
        return float(value)
    return value


def _split_commas(text):
    parts, buf, quote = [], [], None
    for char in text:
        if quote:
            if char == quote:
                quote = None
            buf.append(char)
        elif char in "\"'":
            quote = char
            buf.append(char)
        elif char == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(char)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]
