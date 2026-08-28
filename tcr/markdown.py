"""Convertisseur Markdown maison, taillé pour les besoins d'une revue.

Gère : titres, paragraphes, gras/italique, liens, images légendées, listes
(imbriquées), citations, tableaux, code, filets — plus quatre blocs éditoriaux
propres à TCR (`:::chiffres`, `:::encadre`, `:::citation`, `:::essentiel`) et
les espaces insécables de la typographie française.
"""

import html
import re
import unicodedata

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_HR = re.compile(r"^([-*_])\s*(?:\1\s*){2,}$")
_BULLET = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_FENCE = re.compile(r"^```+\s*([A-Za-z0-9_+-]*)\s*$")
_DIRECTIVE = re.compile(r'^:::\s*([a-zA-Z][a-zA-Z0-9_-]*)\s*(?:"([^"]*)")?\s*$')
_TABLE_SEP = re.compile(r"^\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*$")
_IMAGE_ONLY = re.compile(r'^!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)$')

DIRECTIVE_TITLES = {"essentiel": "L'essentiel"}


def convert(text, section_ids=None):
    """Rend un document Markdown en HTML."""
    lines = text.replace("\r\n", "\n").expandtabs(4).split("\n")
    return "\n".join(_blocks(lines, section_ids if section_ids is not None else []))


def _blocks(lines, ids):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        fence = _FENCE.match(stripped)
        if fence:
            i, block = _code(lines, i, fence.group(1))
            out.append(block)
            continue

        if stripped.startswith(":::"):
            i, block = _directive(lines, i, ids)
            out.append(block)
            continue

        if _HR.match(stripped):
            out.append('<hr class="md-rule">')
            i += 1
            continue

        heading = _HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            slug = _unique(slugify(text), ids)
            out.append(f'<h{level} id="{slug}">{inline(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            i, block = _quote(lines, i, ids)
            out.append(block)
            continue

        if "|" in stripped and i + 1 < n and _TABLE_SEP.match(lines[i + 1].strip()):
            i, block = _table(lines, i)
            out.append(block)
            continue

        if _BULLET.match(line):
            i, block = _list(lines, i, ids)
            out.append(block)
            continue

        if stripped.startswith("<"):
            i, block = _raw_html(lines, i)
            out.append(block)
            continue

        i, block = _paragraph(lines, i)
        out.append(block)
    return out


def _code(lines, i, lang):
    i += 1
    buf = []
    while i < len(lines) and not lines[i].strip().startswith("```"):
        buf.append(lines[i])
        i += 1
    css = f' class="language-{lang}"' if lang else ""
    body = html.escape("\n".join(buf))
    return i + 1, f'<pre class="md-code"><code{css}>{body}</code></pre>'


def _raw_html(lines, i):
    buf = []
    while i < len(lines) and lines[i].strip():
        buf.append(lines[i])
        i += 1
    return i, "\n".join(buf)


def _quote(lines, i, ids):
    buf = []
    while i < len(lines) and lines[i].strip().startswith(">"):
        buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
        i += 1
    inner = "\n".join(_blocks(buf, ids))
    return i, f"<blockquote>{inner}</blockquote>"


def _paragraph(lines, i):
    buf = []
    while i < len(lines) and lines[i].strip() and not _breaks_paragraph(lines[i]):
        buf.append(lines[i].strip())
        i += 1
    text = " ".join(buf)
    picture = _IMAGE_ONLY.match(text)
    if picture:
        alt, src, title = picture.group(1), picture.group(2), picture.group(3)
        caption = title or alt
        figure = (
            f'<figure class="md-figure"><img src="{html.escape(src, quote=True)}" '
            f'alt="{html.escape(alt, quote=True)}" loading="lazy" decoding="async">'
        )
        if caption:
            figure += f"<figcaption>{inline(caption)}</figcaption>"
        return i, figure + "</figure>"
    return i, f"<p>{inline(text)}</p>"


def _breaks_paragraph(line):
    stripped = line.strip()
    return bool(
        _HEADING.match(stripped)
        or _HR.match(stripped)
        or _BULLET.match(line)
        or _FENCE.match(stripped)
        or stripped.startswith((">", ":::"))
    )


def _list(lines, i, ids):
    indent_of = lambda s: len(s) - len(s.lstrip(" "))
    base = indent_of(lines[i])
    ordered = bool(re.match(r"^\s*\d+[.)]\s+", lines[i]))
    items, n = [], len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            nxt = i + 1
            if nxt < n and lines[nxt].strip() and indent_of(lines[nxt]) >= base and _BULLET.match(lines[nxt]):
                i = nxt
                continue
            break
        bullet = _BULLET.match(line)
        if bullet and indent_of(line) == base:
            items.append([bullet.group(3)])
            i += 1
        elif items and indent_of(line) > base:
            items[-1].append(line[base + 2 :] if len(line) > base + 2 else line.strip())
            i += 1
        else:
            break

    rendered = []
    for item in items:
        head, rest = item[0], item[1:]
        if any(_BULLET.match(part) for part in rest):
            nested = "\n".join(_blocks(rest, ids))
            rendered.append(f"<li>{inline(head)}{nested}</li>")
        else:
            joined = " ".join([head] + [p.strip() for p in rest]).strip()
            rendered.append(f"<li>{inline(joined)}</li>")
    tag = "ol" if ordered else "ul"
    return i, f'<{tag} class="md-list">' + "".join(rendered) + f"</{tag}>"


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _table(lines, i):
    head = _cells(lines[i])
    aligns = []
    for spec in _cells(lines[i + 1]):
        if spec.startswith(":") and spec.endswith(":"):
            aligns.append("center")
        elif spec.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    i += 2
    rows = []
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        rows.append(_cells(lines[i]))
        i += 1

    def cell(tag, value, index):
        align = aligns[index] if index < len(aligns) else "left"
        style = f' class="ta-{align}"' if align != "left" else ""
        return f"<{tag}{style}>{inline(value)}</{tag}>"

    thead = "".join(cell("th", value, k) for k, value in enumerate(head))
    body = "".join(
        "<tr>" + "".join(cell("td", value, k) for k, value in enumerate(row)) + "</tr>"
        for row in rows
    )
    return i, (
        '<div class="md-table-wrap"><table class="md-table">'
        f"<thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _directive(lines, i, ids):
    match = _DIRECTIVE.match(lines[i].strip())
    if not match:
        return i + 1, ""
    kind, title = match.group(1).lower(), match.group(2)
    i += 1
    buf = []
    while i < len(lines) and lines[i].strip() != ":::":
        buf.append(lines[i])
        i += 1
    i += 1

    if kind == "chiffres":
        return i, _chiffres(buf, title)
    if kind == "citation":
        body = "\n".join(_blocks(buf, ids))
        credit = f"<figcaption>{inline(title)}</figcaption>" if title else ""
        return i, f'<figure class="pullquote">{body}{credit}</figure>'
    if kind in ("encadre", "essentiel", "alerte"):
        label = title or DIRECTIVE_TITLES.get(kind, "")
        heading = f'<p class="callout__title">{inline(label)}</p>' if label else ""
        body = "\n".join(_blocks(buf, ids))
        return i, f'<aside class="callout callout--{kind}">{heading}{body}</aside>'

    body = "\n".join(_blocks(buf, ids))
    return i, f'<div class="md-{html.escape(kind, quote=True)}">{body}</div>'


def _chiffres(lines, title):
    tiles = []
    for line in lines:
        if not line.strip():
            continue
        value, _, label = line.partition("|")
        tiles.append(
            '<li class="stat"><span class="stat__value">'
            f'{inline(value.strip())}</span><span class="stat__label">'
            f"{inline(label.strip())}</span></li>"
        )
    heading = f'<p class="stats__title">{inline(title)}</p>' if title else ""
    return f'<div class="stats">{heading}<ul class="stats__grid">' + "".join(tiles) + "</ul></div>"


# --- niveau ligne -----------------------------------------------------------

def inline(text):
    """Transforme le balisage en ligne d'un fragment de texte."""
    spans = []

    def stash(match):
        spans.append(match.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)

    text = re.sub(
        r'!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)',
        lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy" decoding="async">',
        text,
    )
    text = re.sub(r"\[([^\]]+)\]\(\s*([^)\s]+)\s*\)", _link, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    text = french_spacing(text)
    text = re.sub(
        r"\x00(\d+)\x00",
        lambda m: f"<code>{html.escape(spans[int(m.group(1))])}</code>",
        text,
    )
    return text


def _link(match):
    label, url = match.group(1), match.group(2)
    external = url.startswith(("http://", "https://"))
    attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return f'<a href="{url}"{attrs}>{label}</a>'


NBSP = "\u00a0"        # espace insécable (avant « : »)
NNBSP = "\u202f"       # espace fine insécable (avant « ; ! ? % » »)


def french_spacing(text):
    """Insère les espaces insécables attendues en typographie française.

    N'agit que si l'auteur a déjà tapé une espace, ce qui laisse intacts les
    « https:// » et autres suites collées.
    """
    text = re.sub(r"[ \t]+:", NBSP + ":", text)
    text = re.sub(r"[ \t]+([;!?%»])", NNBSP + r"\1", text)
    text = re.sub(r"«[ \t]+", "«" + NNBSP, text)
    return text


# --- utilitaires ------------------------------------------------------------

def slugify(text):
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("'", "-").replace("'", "-").replace("&", " et ")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text or "section"


def _unique(slug, seen):
    candidate, n = slug, 2
    while candidate in seen:
        candidate = f"{slug}-{n}"
        n += 1
    seen.append(candidate)
    return candidate


def strip_tags(markup):
    text = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def reading_time(markup, wpm=210):
    words = len(strip_tags(markup).split())
    return max(1, round(words / wpm))
