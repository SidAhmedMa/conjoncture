"""Lecture des fichiers Markdown de content/ et modèle d'article."""

import datetime
import re
from pathlib import Path

from . import frontmatter, markdown
from .config import fr_date, iso_date
from .markdown import french_spacing as _fr


class Article:
    """Un article : ses métadonnées, son corps rendu, son URL."""

    def __init__(self, path, meta, body, site, rubrique_slug):
        self.path = Path(path)
        self.meta = meta
        self.site = site
        self.raw = body

        self.rubrique_slug = meta.get("rubrique") or rubrique_slug
        self.rubrique = site.by_slug.get(self.rubrique_slug)
        self.title = _fr(meta.get("title") or self.path.stem.replace("-", " ").title())
        self.chapeau = _fr(meta.get("chapeau", ""))
        self.date = _as_date(meta.get("date")) or _date_from_name(self.path)
        self.auteur = meta.get("auteur") or "Rédaction TCR"
        self.portee = meta.get("portee") or site.get("portee_default", "")
        self.image = meta.get("image", "")
        self.image_alt = meta.get("image_alt", "")
        self.image_credit = meta.get("image_credit", "")
        self.tags = meta.get("tags") or []
        self.featured = bool(meta.get("a_la_une"))
        self.draft = bool(meta.get("draft"))
        self.slug = meta.get("slug") or _slug_from_name(self.path)

        self.headings = []
        self.body = with_base(markdown.convert(body, self.headings), site.base)
        self.text = markdown.strip_tags(self.body)
        self.lecture = meta.get("lecture") or markdown.reading_time(self.body)
        self.description = meta.get("description") or self.chapeau or _clip(self.text, 165)

    # -- présentation --------------------------------------------------------

    @property
    def url(self):
        return self.site.url(f"/{self.rubrique_slug}/{self.slug}/")

    @property
    def absolute_url(self):
        return self.site.absolute(f"/{self.rubrique_slug}/{self.slug}/")

    @property
    def output_path(self):
        return Path(self.rubrique_slug) / self.slug / "index.html"

    @property
    def date_label(self):
        return fr_date(self.date)

    @property
    def date_short(self):
        return fr_date(self.date, short=True)

    @property
    def date_iso(self):
        return iso_date(self.date)

    @property
    def rubrique_name(self):
        return self.rubrique.name if self.rubrique else self.rubrique_slug

    @property
    def accent(self):
        return self.rubrique.accent if self.rubrique else "#1F4E8C"

    @property
    def icon(self):
        return self.rubrique.icon if self.rubrique else "insights"

    @property
    def image_url(self):
        return self.site.url(self.image) if self.image else ""

    @property
    def excerpt(self):
        return self.chapeau or _clip(self.text, 180)

    def summary(self, limit=200):
        return _clip(self.text, limit)


class Page:
    """Page fixe (à propos, contact, mentions légales)."""

    def __init__(self, path, meta, body, site):
        self.path = Path(path)
        self.meta = meta
        self.site = site
        self.title = _fr(meta.get("title") or self.path.stem.replace("-", " ").capitalize())
        self.slug = meta.get("slug") or self.path.stem
        self.chapeau = _fr(meta.get("chapeau", ""))
        self.headings = []
        self.body = with_base(markdown.convert(body, self.headings), site.base)
        self.description = meta.get("description") or self.chapeau
        self.draft = bool(meta.get("draft"))

    @property
    def url(self):
        return self.site.url(f"/{self.slug}/")

    @property
    def output_path(self):
        return Path(self.slug) / "index.html"


def load_articles(site, include_drafts=False):
    """Charge tous les articles, du plus récent au plus ancien."""
    articles, seen = [], {}
    root = site.root / "content"
    for rubrique in site.rubriques:
        folder = root / rubrique.slug
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            meta, body = frontmatter.split(path.read_text(encoding="utf-8"))
            article = Article(path, meta, body, site, rubrique.slug)
            if article.draft and not include_drafts:
                continue
            key = (article.rubrique_slug, article.slug)
            if key in seen:
                raise ValueError(
                    f"URL en double /{key[0]}/{key[1]}/ : {seen[key]} et {path}"
                )
            seen[key] = path
            articles.append(article)
    articles.sort(key=lambda a: (a.date or datetime.date.min, a.title), reverse=True)
    return articles


def load_pages(site, include_drafts=False):
    folder = site.root / "content" / "pages"
    pages = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.md")):
            meta, body = frontmatter.split(path.read_text(encoding="utf-8"))
            page = Page(path, meta, body, site)
            if page.draft and not include_drafts:
                continue
            pages.append(page)
    return pages


def by_rubrique(articles, slug):
    return [a for a in articles if a.rubrique_slug == slug]


def related(article, articles, limit=3):
    """Articles proches : même rubrique d'abord, puis tags en commun."""
    pool = [a for a in articles if a is not article]
    tags = {str(t).lower() for t in article.tags}

    def score(other):
        points = 3 if other.rubrique_slug == article.rubrique_slug else 0
        points += 2 * len(tags & {str(t).lower() for t in other.tags})
        return points

    ranked = sorted(pool, key=lambda a: (-score(a), -(a.date or datetime.date.min).toordinal()))
    return [a for a in ranked if score(a) > 0][:limit] or ranked[:limit]


def with_base(markup, base):
    """Préfixe du sous-répertoire de publication les liens absolus rédigés
    dans le Markdown (« /contact/ »), sans toucher aux URL externes ni aux
    adresses protocole-relatives."""
    if not base:
        return markup
    return re.sub(r'((?:href|src)=")/(?!/)', r"\g<1>" + base + "/", markup)


def _as_date(value):
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def _date_from_name(path):
    found = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", path.name)
    if found:
        try:
            return datetime.date(*(int(g) for g in found.groups()))
        except ValueError:
            return None
    return None


def _slug_from_name(path):
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)


def _clip(text, limit):
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.")
    return cut + "…"
