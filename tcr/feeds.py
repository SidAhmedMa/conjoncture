"""Flux RSS, sitemap, robots.txt et index de recherche."""

import datetime
import json
import unicodedata
from xml.sax.saxutils import escape as xml_escape

RFC822_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
RFC822_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def rfc822(date):
    if not date:
        return ""
    stamp = datetime.datetime.combine(date, datetime.time(9, 0))
    return (
        f"{RFC822_DAYS[stamp.weekday()]}, {stamp.day:02d} "
        f"{RFC822_MONTHS[stamp.month - 1]} {stamp.year} "
        f"{stamp:%H:%M:%S} +0000"
    )


def rss(site, articles, limit=30):
    now = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for article in articles[:limit]:
        items.append(
            "    <item>\n"
            f"      <title>{xml_escape(article.title)}</title>\n"
            f"      <link>{xml_escape(article.absolute_url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{xml_escape(article.absolute_url)}</guid>\n"
            f"      <pubDate>{rfc822(article.date)}</pubDate>\n"
            f"      <category>{xml_escape(article.rubrique_name)}</category>\n"
            f"      <description>{xml_escape(article.description)}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{xml_escape(site.title)}</title>\n"
        f"    <link>{xml_escape(site.absolute('/'))}</link>\n"
        f"    <description>{xml_escape(site.description)}</description>\n"
        f"    <language>{site.get('lang', 'fr')}</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link href="{xml_escape(site.absolute("/flux.xml"))}" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def sitemap(site, urls):
    entries = []
    for path, lastmod in urls:
        loc = xml_escape(site.absolute(path))
        stamp = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        entries.append(f"  <url><loc>{loc}</loc>{stamp}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def robots(site):
    if site.get("noindex"):
        return "# Déploiement de relecture — non destiné à l'indexation\nUser-agent: *\nDisallow: /\n"
    return (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {site.absolute('/sitemap.xml')}\n"
    )


def fold(text):
    """Minuscule sans accents, pour une recherche tolérante."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def search_index(site, articles):
    records = []
    for article in articles:
        haystack = " ".join(
            [article.title, article.excerpt, article.rubrique_name,
             " ".join(str(t) for t in article.tags), article.text[:1200]]
        )
        records.append(
            {
                "t": article.title,
                "u": article.url,
                "r": article.rubrique_name,
                "rs": article.rubrique_slug,
                "a": article.accent,
                "d": article.date_short,
                "iso": article.date_iso,
                "m": article.lecture,
                "e": article.excerpt,
                "k": fold(haystack),
            }
        )
    return json.dumps(records, ensure_ascii=False, separators=(",", ":"))
