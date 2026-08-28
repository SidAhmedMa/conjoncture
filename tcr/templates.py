"""Moteur de gabarits minimal : substitution + conditions.

    {{ cle }}            insère la valeur telle quelle (HTML autorisé)
    {{ cle|e }}          insère la valeur échappée (attributs, texte brut)
    {{#if cle}}…{{/if}}  bloc conditionnel, avec {{else}} facultatif
    {{#if !cle}}…{{/if}} condition inversée

Les boucles sont volontairement absentes : les listes sont pré-rendues côté
Python puis passées comme un unique fragment HTML.
"""

import html
import re
from pathlib import Path

_VAR = re.compile(r"\{\{\s*([^#/][^}]*?)\s*\}\}")
_IF = re.compile(r"\{\{#if\s+([^}]+?)\s*\}\}")
_TOKEN = re.compile(r"\{\{#if\s+[^}]+?\}\}|\{\{else\}\}|\{\{/if\}\}")


class Templates:
    """Charge et met en cache les gabarits d'un répertoire."""

    def __init__(self, root):
        self.root = Path(root)
        self._cache = {}

    def load(self, name):
        if name not in self._cache:
            path = self.root / name
            if not path.exists():
                raise FileNotFoundError(f"gabarit introuvable : {path}")
            self._cache[name] = path.read_text(encoding="utf-8")
        return self._cache[name]

    def render(self, name, context):
        return render(self.load(name), context)

    def clear(self):
        self._cache.clear()


def render(template, context):
    return _substitute(_conditionals(template, context), context)


def _substitute(template, context):
    def replace(match):
        expr = match.group(1).strip()
        escape = expr.endswith("|e")
        if escape:
            expr = expr[:-2].strip()
        value = context.get(expr, "")
        if value is None or value is False:
            value = ""
        value = str(value)
        return html.escape(value, quote=True) if escape else value

    return _VAR.sub(replace, template)


def _conditionals(template, context):
    out, pos = [], 0
    while True:
        opener = _IF.search(template, pos)
        if not opener:
            out.append(template[pos:])
            return "".join(out)

        out.append(template[pos : opener.start()])
        key = opener.group(1).strip()
        negate = key.startswith("!")
        if negate:
            key = key[1:].strip()

        depth, cursor, else_span, end_span = 1, opener.end(), None, None
        while depth:
            token = _TOKEN.search(template, cursor)
            if not token:
                raise ValueError(f"{{{{#if {key}}}}} non refermé")
            text = token.group(0)
            if text.startswith("{{#if"):
                depth += 1
            elif text == "{{else}}":
                if depth == 1:
                    else_span = token.span()
            else:
                depth -= 1
                if depth == 0:
                    end_span = token.span()
            cursor = token.end()

        if else_span:
            when_true = template[opener.end() : else_span[0]]
            when_false = template[else_span[1] : end_span[0]]
        else:
            when_true, when_false = template[opener.end() : end_span[0]], ""

        value = context.get(key)
        truthy = bool(value) and value != ""
        if negate:
            truthy = not truthy
        out.append(_conditionals(when_true if truthy else when_false, context))
        pos = end_span[1]
