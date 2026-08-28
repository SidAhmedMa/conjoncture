"""Construction des pages HTML à partir des gabarits et du contenu."""

import datetime
import html
import json
import re
from urllib.parse import quote

from . import content as content_mod
from .icons import icon
from .templates import Templates

_HEADINGS = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>', re.S)


class Renderer:
    def __init__(self, site, articles, pages):
        self.site = site
        self.articles = articles
        self.pages = pages
        self.tpl = Templates(site.root / "templates")
        self.year = datetime.date.today().year

    # -- fragments réutilisables --------------------------------------------

    def chip(self, article_or_rubrique, size=16):
        item = article_or_rubrique
        rubrique = getattr(item, "rubrique", item)
        if rubrique is None:
            return ""
        return self.tpl.render(
            "partials/chip.html",
            {
                "rubrique_url": rubrique.url,
                "rubrique_name": rubrique.name,
                "accent": rubrique.accent,
                "icon": icon(rubrique.icon, size, "icon"),
            },
        )

    def media(self, article, sizes="", eager=False):
        """Visuel d'article : image réelle, ou repère graphique de rubrique."""
        if article.image:
            loading = "eager" if eager else "lazy"
            alt = html.escape(article.image_alt or article.title, quote=True)
            attrs = f' sizes="{sizes}"' if sizes else ""
            return (
                f'<img class="media__img" src="{html.escape(article.image_url, quote=True)}" '
                f'alt="{alt}" loading="{loading}" decoding="async"{attrs}>'
            )
        return (
            f'<span class="media__ph" style="--accent: {article.accent}" aria-hidden="true">'
            f'{icon(article.icon, 64, "media__phIcon", stroke=1.1)}'
            f'<span class="media__phMesh"></span></span>'
        )

    def metarow(self, article):
        return self.tpl.render(
            "partials/metarow.html",
            {
                "icon_calendar": icon("calendrier", 20),
                "icon_clock": icon("horloge", 20),
                "icon_globe": icon("globe", 20),
                "date_iso": article.date_iso,
                "date_label": article.date_label,
                "lecture": article.lecture,
                "portee": article.portee,
            },
        )

    def card(self, article, eager=False):
        return self.tpl.render(
            "partials/card.html",
            {
                "url": article.url,
                "title": article.title,
                "excerpt": article.excerpt,
                "accent": article.accent,
                "chip": self.chip(article),
                "media": self.media(article, "(max-width: 700px) 92vw, 33vw", eager),
                "date_iso": article.date_iso,
                "date_short": article.date_short,
                "lecture": article.lecture,
            },
        )

    def cards(self, articles, eager_first=False):
        return "\n".join(
            self.card(a, eager=(eager_first and i == 0)) for i, a in enumerate(articles)
        )

    def tease(self, article):
        return self.tpl.render(
            "partials/tease.html",
            {
                "url": article.url,
                "title": article.title,
                "accent": article.accent,
                "rubrique_name": article.rubrique_name,
                "date_iso": article.date_iso,
                "date_short": article.date_short,
                "lecture": article.lecture,
            },
        )

    def teases(self, articles):
        return "\n".join(self.tease(a) for a in articles)

    def hero(self, article):
        return self.tpl.render(
            "partials/hero.html",
            {
                "url": article.url,
                "title": article.title,
                "chapeau": article.chapeau or article.summary(190),
                "accent": article.accent,
                "chip": self.chip(article, 18),
                "metarow": self.metarow(article),
                "media": self.media(article, "(max-width: 900px) 100vw, 58vw", eager=True),
                "icon_arrow": icon("fleche", 18),
            },
        )

    def sechead(self, rubrique):
        return self.tpl.render(
            "partials/sechead.html",
            {
                "chip": self.chip(rubrique, 18),
                "keywords": rubrique.keywords,
                "rubrique_url": rubrique.url,
                "icon_arrow": icon("fleche", 18),
            },
        )

    def newsletter(self):
        return self.tpl.render(
            "partials/newsletter.html",
            {
                "icon_arrow": icon("fleche", 18),
                "newsletter_action": self.site.get("newsletter_action", "#"),
            },
        )

    # -- enveloppe -----------------------------------------------------------

    def logo_mark(self, variant=""):
        png = self.site.root / "assets" / "img" / "logo-mark.png"
        if png.exists():
            return (
                f'<img class="mark mark--img{variant}" src="{self.site.url("/assets/img/logo-mark.png")}" '
                f'alt="{html.escape(self.site.title, quote=True)}" width="44" height="44">'
            )
        return (
            f'<span class="mark{variant}" aria-hidden="true"><span class="mark__text">'
            f'{html.escape(self.site.short_title)}</span></span>'
        )

    def logo_wordmark(self):
        png = self.site.root / "assets" / "img" / "logo-wordmark.png"
        if png.exists():
            return (
                f'<img class="wordmark wordmark--img" src="{self.site.url("/assets/img/logo-wordmark.png")}" '
                f'alt="{html.escape(self.site.title, quote=True)}" height="22">'
            )
        return f'<span class="wordmark">{html.escape(self.site.title)}</span>'

    def nav_links(self, current=""):
        out = []
        for rubrique in self.site.rubriques:
            active = ' aria-current="page"' if rubrique.slug == current else ""
            state = " is-active" if rubrique.slug == current else ""
            out.append(
                f'<a class="rubnav__link{state}" style="--accent: {rubrique.accent}" '
                f'href="{rubrique.url}"{active}>{icon(rubrique.icon, 17)}'
                f"<span>{html.escape(rubrique.name)}</span></a>"
            )
        return "\n".join(out)

    def footer_cols(self):
        cols = [
            '<div class="footer__col"><p class="footer__colTitle">Rubriques</p><ul>'
            + "".join(
                f'<li><a href="{r.url}">{html.escape(r.name)}</a></li>'
                for r in self.site.rubriques
            )
            + "</ul></div>",
            '<div class="footer__col"><p class="footer__colTitle">Explorer</p><ul>'
            f'<li><a href="{self.site.url("/archives/")}">Archives</a></li>'
            f'<li><a href="{self.site.url("/recherche/")}">Recherche</a></li>'
            f'<li><a href="{self.site.url("/flux.xml")}">Flux RSS</a></li>'
            "</ul></div>",
            '<div class="footer__col"><p class="footer__colTitle">La revue</p><ul>'
            + "".join(
                f'<li><a href="{self.site.url(l["url"])}">{html.escape(l["label"])}</a></li>'
                for l in self.site.get("legal_links", [])
            )
            + f'<li><a href="mailto:{html.escape(self.site.get("email", ""))}">Nous écrire</a></li>'
            "</ul></div>",
        ]
        return "\n".join(cols)

    def social_links(self):
        out = []
        for entry in self.site.get("social", []):
            url = self.site.url(entry["url"])
            out.append(
                f'<li><a class="social__link" href="{html.escape(url, quote=True)}" '
                f'aria-label="{html.escape(entry["name"], quote=True)}" '
                f'title="{html.escape(entry["name"], quote=True)}">{icon(entry.get("icon", "fleche"), 18)}</a></li>'
            )
        return "\n".join(out)

    def legal_links(self):
        return "".join(
            f'<li><a href="{self.site.url(l["url"])}">{html.escape(l["label"])}</a></li>'
            for l in self.site.get("legal_links", [])
        )

    def shell(self, content, *, title, description, path, current="", body_class="",
              og_image="", og_type="website", og_title=None, jsonld=None):
        site_title = self.site.title
        page_title = title if title == site_title else f"{title} — {site_title}"
        return self.tpl.render(
            "base.html",
            {
                "lang": self.site.get("lang", "fr"),
                "locale": self.site.get("locale", "fr_FR"),
                "base": self.site.base,
                "site_title": site_title,
                "tagline": self.site.tagline,
                "page_title": page_title,
                "og_title": og_title or title,
                "description": description or self.site.description,
                "canonical": self.site.absolute(path),
                "og_image": og_image,
                "og_type": og_type,
                "twitter_card": "summary_large_image" if og_image else "summary",
                "body_class": body_class,
                "content": content,
                "nav_links": self.nav_links(current),
                "logo_mark": self.logo_mark(),
                "logo_mark_light": self.logo_mark(" mark--light"),
                "logo_wordmark": self.logo_wordmark(),
                "footer_note": self.site.get("footer_note", ""),
                "footer_cols": self.footer_cols(),
                "social_links": self.social_links(),
                "legal_links": self.legal_links(),
                "year": self.year,
                "icon_search": icon("recherche", 20),
                "icon_menu": icon("menu", 22),
                "icon_close": icon("fermer", 20),
                "icon_top": icon("haut", 20),
                "jsonld": json.dumps(jsonld, ensure_ascii=False) if jsonld else "",
                "noindex": self.site.get("noindex", False),
            },
        )

    # -- pages ---------------------------------------------------------------

    def home(self):
        articles = self.articles
        featured = next((a for a in articles if a.featured), articles[0] if articles else None)
        rest = [a for a in articles if a is not featured]

        sections = []
        for rubrique in self.site.rubriques:
            if rubrique.slug == "tcr-insights":
                continue
            items = content_mod.by_rubrique(rest, rubrique.slug)[:3]
            if not items:
                continue
            sections.append(
                '<section class="band band--rub">'
                f'<div class="wrap">{self.sechead(rubrique)}'
                f'<div class="grid grid--3">{self.cards(items)}</div></div></section>'
            )

        insights_rub = self.site.by_slug.get("tcr-insights")
        insights_items = content_mod.by_rubrique(rest, "tcr-insights")[:3] if insights_rub else []
        insights_band = ""
        if insights_items:
            insights_band = (
                '<section class="band band--dark">'
                f'<div class="wrap">{self.sechead(insights_rub)}'
                f'<div class="grid grid--3">{self.cards(insights_items)}</div></div></section>'
            )

        body = self.tpl.render(
            "home.html",
            {
                "base": self.site.base,
                "hero": self.hero(featured) if featured else "",
                "latest_cards": self.cards(rest[:4]),
                "fil": self.teases(rest[4:11]),
                "rubrique_sections": "\n".join(sections),
                "insights_band": insights_band,
                "newsletter": self.newsletter(),
                "icon_arrow": icon("fleche", 18),
            },
        )
        return self.shell(
            body,
            title=self.site.title,
            description=self.site.description,
            path="/",
            body_class="page-home",
            og_image=self.site.absolute(featured.image) if featured and featured.image else "",
            jsonld={
                "@context": "https://schema.org",
                "@type": "NewsMediaOrganization",
                "name": self.site.title,
                "url": self.site.get("url", ""),
                "description": self.site.description,
                "email": self.site.get("email", ""),
                "sameAs": [s["url"] for s in self.site.get("social", []) if s["url"].startswith("http")],
            },
        )

    def rubrique_page(self, rubrique, items, page_no, total_pages):
        lead = ""
        grid = items
        if page_no == 1 and items:
            lead, grid = self.card(items[0], eager=True), items[1:]
            lead = f'<div class="grid grid--lead">{lead}</div>'
        count = len(content_mod.by_rubrique(self.articles, rubrique.slug))
        path = f"/{rubrique.slug}/" if page_no == 1 else f"/{rubrique.slug}/page/{page_no}/"
        body = self.tpl.render(
            "rubrique.html",
            {
                "base": self.site.base,
                "rubrique_name": rubrique.name,
                "rubrique_desc": rubrique.description,
                "keywords": rubrique.keywords,
                "accent": rubrique.accent,
                "icon_big": icon(rubrique.icon, 34, "icon", stroke=1.4),
                "count_label": _plural(count, "article publié", "articles publiés"),
                "lead": lead,
                "cards": self.cards(grid),
                "pagination": self.pagination(rubrique, page_no, total_pages),
                "newsletter": self.newsletter(),
            },
        )
        return self.shell(
            body,
            title=rubrique.name if page_no == 1 else f"{rubrique.name} — page {page_no}",
            description=rubrique.description,
            path=path,
            current=rubrique.slug,
            body_class="page-rubrique",
        )

    def pagination(self, rubrique, page_no, total_pages):
        if total_pages <= 1:
            return ""
        link = lambda n: (
            self.site.url(f"/{rubrique.slug}/") if n == 1
            else self.site.url(f"/{rubrique.slug}/page/{n}/")
        )
        parts = ['<nav class="pager" aria-label="Pagination">']
        if page_no > 1:
            parts.append(f'<a class="pager__nav" href="{link(page_no - 1)}" rel="prev">Précédent</a>')
        for n in range(1, total_pages + 1):
            state = ' aria-current="page" class="pager__num is-active"' if n == page_no else ' class="pager__num"'
            parts.append(f'<a{state} href="{link(n)}">{n}</a>')
        if page_no < total_pages:
            parts.append(f'<a class="pager__nav" href="{link(page_no + 1)}" rel="next">Suivant</a>')
        parts.append("</nav>")
        return "".join(parts)

    def article_page(self, article):
        figure = ""
        if article.image:
            credit = (
                f'<figcaption class="credit">{html.escape(article.image_credit)}</figcaption>'
                if article.image_credit else ""
            )
            figure = (
                f'<figure class="hero-figure">{self.media(article, "100vw", eager=True)}{credit}</figure>'
            )
        tags = "".join(
            f'<li><a href="{self.site.url("/recherche/")}?q={quote(str(t))}">#{html.escape(str(t))}</a></li>'
            for t in article.tags
        )
        related = content_mod.related(article, self.articles, 3)
        body = self.tpl.render(
            "article.html",
            {
                "base": self.site.base,
                "accent": article.accent,
                "title": article.title,
                "chapeau": article.chapeau,
                "rubrique_url": article.rubrique.url if article.rubrique else self.site.base + "/",
                "rubrique_name": article.rubrique_name,
                "chip": self.chip(article, 18),
                "metarow": self.metarow(article),
                "auteur": article.auteur,
                "icon_pen": icon("plume", 16),
                "figure": figure,
                "toc": self.toc(article.body),
                "share_links": self.share(article),
                "body": article.body,
                "tags": tags,
                "related": self.cards(related),
                "icon_arrow": icon("fleche", 18),
                "newsletter": self.newsletter(),
            },
        )
        return self.shell(
            body,
            title=article.title,
            description=article.description,
            path=f"/{article.rubrique_slug}/{article.slug}/",
            current=article.rubrique_slug,
            body_class="page-article",
            og_type="article",
            og_image=self.site.absolute(article.image) if article.image else "",
            jsonld={
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": article.title,
                "description": article.description,
                "datePublished": article.date_iso,
                "articleSection": article.rubrique_name,
                "inLanguage": self.site.get("lang", "fr"),
                "author": {"@type": "Organization", "name": article.auteur},
                "publisher": {"@type": "Organization", "name": self.site.title},
                "mainEntityOfPage": article.absolute_url,
                **({"image": [self.site.absolute(article.image)]} if article.image else {}),
                **({"keywords": ", ".join(str(t) for t in article.tags)} if article.tags else {}),
            },
        )

    def toc(self, body_html):
        items = [
            (int(level), slug, re.sub(r"<[^>]+>", "", text).strip())
            for level, slug, text in _HEADINGS.findall(body_html)
        ]
        if len(items) < 2:
            return ""
        rows = "".join(
            f'<li class="toc__item toc__item--h{level}"><a href="#{slug}">{html.escape(text)}</a></li>'
            for level, slug, text in items
        )
        return f'<ol class="toc__list">{rows}</ol>'

    def share(self, article):
        url = quote(article.absolute_url, safe="")
        title = quote(article.title)
        targets = [
            ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={url}", "linkedin"),
            ("X", f"https://x.com/intent/tweet?url={url}&text={title}", "x"),
            ("E-mail", f"mailto:?subject={title}&body={url}", "lettre"),
        ]
        out = [
            f'<li><a class="share__link" href="{href}" aria-label="Partager sur {name}" '
            f'title="Partager sur {name}"{" target=\"_blank\" rel=\"noopener\"" if href.startswith("http") else ""}>'
            f"{icon(ico, 18)}</a></li>"
            for name, href, ico in targets
        ]
        out.append(
            f'<li><button class="share__link" type="button" data-copy="{html.escape(article.absolute_url, quote=True)}" '
            f'aria-label="Copier le lien" title="Copier le lien">{icon("lien", 18)}</button></li>'
        )
        return "".join(out)

    def static_page(self, page):
        body = self.tpl.render(
            "page.html",
            {
                "base": self.site.base,
                "title": page.title,
                "chapeau": page.chapeau,
                "body": page.body,
            },
        )
        return self.shell(
            body,
            title=page.title,
            description=page.description,
            path=f"/{page.slug}/",
            body_class="page-static",
        )

    def archives(self):
        buckets = {}
        for article in self.articles:
            year = article.date.year if article.date else "—"
            buckets.setdefault(year, []).append(article)
        blocks = []
        for year in sorted(buckets, key=lambda y: (y != "—", y), reverse=True):
            rows = "".join(
                f'<li class="arch__row" data-rub="{a.rubrique_slug}" style="--accent: {a.accent}">'
                f'<a href="{a.url}"><time datetime="{a.date_iso}">{html.escape(a.date_short)}</time>'
                f'<span class="arch__rub">{html.escape(a.rubrique_name)}</span>'
                f'<span class="arch__title">{html.escape(a.title)}</span>'
                f'<span class="arch__min">{a.lecture} min</span></a></li>'
                for a in buckets[year]
            )
            blocks.append(
                f'<section class="arch" data-year="{year}"><h2 class="arch__year">{year}</h2>'
                f'<ul class="arch__list">{rows}</ul></section>'
            )
        filters = "".join(
            f'<button class="filters__btn" type="button" data-filter="{r.slug}" '
            f'style="--accent: {r.accent}">{html.escape(r.name)}</button>'
            for r in self.site.rubriques
        )
        body = self.tpl.render(
            "archives.html",
            {
                "base": self.site.base,
                "count_label": _plural(len(self.articles), "article", "articles"),
                "filter_buttons": filters,
                "years": "\n".join(blocks) or '<p class="empty">Aucun article pour le moment.</p>',
            },
        )
        return self.shell(
            body,
            title="Archives",
            description=f"Toutes les publications de {self.site.title}.",
            path="/archives/",
            body_class="page-archives",
        )

    def recherche(self):
        body = self.tpl.render(
            "recherche.html",
            {"base": self.site.base, "icon_search": icon("recherche", 20)},
        )
        return self.shell(
            body,
            title="Recherche",
            description=f"Rechercher un article dans {self.site.title}.",
            path="/recherche/",
            body_class="page-recherche",
        )

    def notfound(self):
        chips = "".join(self.chip(r, 18) for r in self.site.rubriques)
        body = self.tpl.render(
            "404.html",
            {"base": self.site.base, "icon_arrow": icon("fleche", 18), "chips": chips},
        )
        return self.shell(
            body,
            title="Page introuvable",
            description="La page demandée n'existe pas.",
            path="/404.html",
            body_class="page-404",
        )


def _plural(count, singular, plural):
    return f"{count} {singular if count <= 1 else plural}"
