#!/usr/bin/env python3
"""The Conjoncture Review — générateur de site statique.

    python3 build.py                 construit le site dans dist/
    python3 build.py --serve         construit puis sert sur http://localhost:8000
    python3 build.py --serve --watch reconstruit à chaque modification
    python3 build.py --drafts        inclut les brouillons (draft: true)
    python3 build.py new "Titre" -r energie    crée un nouvel article

Aucune dépendance : bibliothèque standard Python 3.11+ uniquement.
"""

import argparse
import datetime
import http.server
import math
import shutil
import socketserver
import subprocess
import sys
import threading
import time
from functools import partial
from pathlib import Path

from tcr import feeds
from tcr.config import Site
from tcr.content import by_rubrique, load_articles, load_pages
from tcr.markdown import slugify
from tcr.render import Renderer

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="32" r="32" fill="#1c2c3a"/>
<text x="32" y="41" text-anchor="middle" fill="#ffffff" font-size="21"
 letter-spacing="1.2" font-family="Verdana, DejaVu Sans, sans-serif">TCR</text>
</svg>
"""


def build(include_drafts=False, quiet=False):
    started = time.perf_counter()
    site = Site.load(ROOT)
    articles = load_articles(site, include_drafts)
    pages = load_pages(site, include_drafts)
    renderer = Renderer(site, articles, pages)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    written, urls = 0, []

    def emit(relpath, text):
        nonlocal written
        target = DIST / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written += 1

    emit("index.html", renderer.home())
    urls.append(("/", _today()))

    per_page = int(site.get("per_page", 12)) or 12
    for rubrique in site.rubriques:
        items = by_rubrique(articles, rubrique.slug)
        total_pages = max(1, math.ceil(len(items) / per_page))
        for page_no in range(1, total_pages + 1):
            chunk = items[(page_no - 1) * per_page : page_no * per_page]
            html = renderer.rubrique_page(rubrique, chunk, page_no, total_pages)
            if page_no == 1:
                emit(f"{rubrique.slug}/index.html", html)
                urls.append((f"/{rubrique.slug}/", _today()))
            else:
                emit(f"{rubrique.slug}/page/{page_no}/index.html", html)
                urls.append((f"/{rubrique.slug}/page/{page_no}/", _today()))

    for article in articles:
        emit(str(article.output_path), renderer.article_page(article))
        urls.append((f"/{article.rubrique_slug}/{article.slug}/", article.date_iso))

    for page in pages:
        emit(str(page.output_path), renderer.static_page(page))
        urls.append((f"/{page.slug}/", _today()))

    emit("archives/index.html", renderer.archives())
    emit("recherche/index.html", renderer.recherche())
    emit("404.html", renderer.notfound())
    urls += [("/archives/", _today()), ("/recherche/", _today())]

    emit("flux.xml", feeds.rss(site, articles))
    emit("sitemap.xml", feeds.sitemap(site, urls))
    emit("robots.txt", feeds.robots(site))
    emit("recherche/index.json", feeds.search_index(site, articles))

    _copy_assets(site)
    _write_favicon()

    if not quiet:
        elapsed = (time.perf_counter() - started) * 1000
        drafts = " (brouillons inclus)" if include_drafts else ""
        print(
            f"✓ {written} fichiers · {len(articles)} articles · "
            f"{len(pages)} pages · {len(site.rubriques)} rubriques{drafts} "
            f"— {elapsed:.0f} ms → dist/"
        )
    return site, articles


def _copy_assets(site):
    source = ROOT / "assets"
    if source.is_dir():
        shutil.copytree(source, DIST / "assets", dirs_exist_ok=True)
    for extra in ("CNAME", ".nojekyll", "_headers", "_redirects"):
        candidate = ROOT / extra
        if candidate.is_file():
            shutil.copy2(candidate, DIST / extra)


def _write_favicon():
    target = DIST / "assets" / "img" / "favicon.svg"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FAVICON, encoding="utf-8")


def _today():
    return datetime.date.today().isoformat()


# --- nouvel article ---------------------------------------------------------

TEMPLATE = """---
title: "{title}"
rubrique: {rubrique}
date: {date}
chapeau: "Une phrase de présentation qui résume l'enjeu de l'article."
auteur: "Rédaction TCR"
portee: "{portee}"
tags: []
image: ""
image_alt: ""
image_credit: ""
a_la_une: false
draft: true
---

## Contexte

Premier paragraphe.

::: chiffres "Repères"
0 | Premier indicateur
0 | Deuxième indicateur
:::

## Analyse

Développement.

::: essentiel
- Point clé.
- Point clé.
:::
"""


def new_article(title, rubrique, date=None):
    site = Site.load(ROOT)
    if rubrique not in site.by_slug:
        options = ", ".join(site.by_slug)
        raise SystemExit(f"Rubrique inconnue « {rubrique} ». Choix possibles : {options}")
    day = date or datetime.date.today().isoformat()
    slug = slugify(title)
    path = ROOT / "content" / rubrique / f"{day}-{slug}.md"
    if path.exists():
        raise SystemExit(f"Le fichier existe déjà : {path}")
    path.write_text(
        TEMPLATE.format(
            title=title.replace('"', "'"),
            rubrique=rubrique,
            date=day,
            portee=site.get("portee_default", ""),
        ),
        encoding="utf-8",
    )
    print(f"✓ créé {path.relative_to(ROOT)}")
    print(f"  URL une fois publié : /{rubrique}/{slug}/")
    print("  Retirez « draft: true » pour le publier.")


# --- serveur ----------------------------------------------------------------

class Handler(http.server.SimpleHTTPRequestHandler):
    """Sert dist/ avec des URL propres et une vraie page 404."""

    def log_message(self, fmt, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = DIST / "404.html"
            if page.exists():
                body = page.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)


def serve(port, include_drafts, watch):
    handler = partial(Handler, directory=str(DIST))
    socketserver.TCPServer.allow_reuse_address = True
    if watch:
        threading.Thread(target=_watch, args=(include_drafts,), daemon=True).start()
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"→ http://localhost:{port}   (Ctrl+C pour arrêter)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArrêt du serveur.")


def _snapshot():
    watched = []
    for folder in ("content", "templates", "assets", "tcr"):
        watched += list((ROOT / folder).rglob("*"))
    watched += [ROOT / "site.json", ROOT / "build.py"]
    watched = [p for p in watched if "__pycache__" not in p.parts]
    return {p: p.stat().st_mtime for p in watched if p.is_file()}


def _watch(include_drafts):
    """Reconstruit dans un sous-processus : les modifications de code sont prises
    en compte au même titre que celles du contenu, sans redémarrer le serveur."""
    previous = _snapshot()
    while True:
        time.sleep(0.6)
        try:
            current = _snapshot()
        except OSError:
            continue
        if current == previous:
            continue
        previous = current
        command = [sys.executable, str(ROOT / "build.py")]
        if include_drafts:
            command.append("--drafts")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        stamp = f"{datetime.datetime.now():%H:%M:%S}"
        if result.returncode == 0:
            print(f"↻ {stamp} — {result.stdout.strip()}")
        else:
            print(f"✗ {stamp} — échec de la construction :\n{result.stderr.strip()}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Générateur de The Conjoncture Review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("new", help="créer un article pré-rempli")
    create.add_argument("title", help="titre de l'article")
    create.add_argument("-r", "--rubrique", required=True, help="slug de la rubrique")
    create.add_argument("-d", "--date", help="date AAAA-MM-JJ (défaut : aujourd'hui)")

    parser.add_argument("--serve", action="store_true", help="servir dist/ après construction")
    parser.add_argument("--watch", action="store_true", help="reconstruire à chaque modification")
    parser.add_argument("--port", type=int, default=8000, help="port du serveur (défaut 8000)")
    parser.add_argument("--drafts", action="store_true", help="inclure les brouillons")

    args = parser.parse_args(argv)

    if args.command == "new":
        new_article(args.title, args.rubrique, args.date)
        return 0

    build(args.drafts)
    if args.serve:
        serve(args.port, args.drafts, args.watch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
