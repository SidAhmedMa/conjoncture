"""Pictogrammes SVG en trait, dessinés au gabarit 24×24."""

_PATHS = {
    "economie": '<path d="M3 3v18h18"/><polyline points="7 14 11 10 14 13 20 7"/><polyline points="20 11.5 20 7 15.5 7"/>',
    "energie": '<path d="M13 2 4.5 13.5H10L9 22l8.5-11.5H12L13 2z"/>',
    "infrastructures": '<path d="M2 20h20"/><path d="M5.5 20v-6.5"/><path d="M18.5 20v-6.5"/><path d="M2 13.5c3.5 0 5.5-6.5 10-6.5s6.5 6.5 10 6.5"/><path d="M12 7v13"/>',
    "mines": '<path d="M2 4h2.2l1.3 3.2"/><path d="M4.6 7.2h16.6l-2.4 8.6H7.1L4.6 7.2z"/><circle cx="9.4" cy="19" r="1.7"/><circle cx="16.6" cy="19" r="1.7"/>',
    "insights": '<circle cx="10.5" cy="10.5" r="7"/><path d="m20.5 20.5-4.6-4.6"/><path d="M8 12v2"/><path d="M10.5 8.5V14"/><path d="M13 10.5V14"/>',
    "calendrier": '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M8 3v4M16 3v4M3 10.5h18"/>',
    "horloge": '<circle cx="12" cy="12" r="9"/><path d="M12 6.8V12l3.4 2"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.6 3.9 5.6 3.9 9S14.6 18.4 12 21c-2.6-2.6-3.9-5.6-3.9-9S9.4 5.6 12 3z"/>',
    "recherche": '<circle cx="10.7" cy="10.7" r="7"/><path d="m20.5 20.5-4.8-4.8"/>',
    "fleche": '<path d="M4.5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "fermer": '<path d="m6 6 12 12M18 6 6 18"/>',
    "plume": '<path d="M4 20 20 4"/><path d="M14 4h6v6"/><path d="M4 20h5l11-11"/>',
    "lettre": '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7.5 10.5V17"/><path d="M7.5 7.4v.1"/><path d="M11.5 17v-3.6a2.4 2.4 0 0 1 4.8 0V17"/><path d="M11.5 10.5V17"/>',
    "x": '<path d="M4 4l16 16M20 4 4 20"/>',
    "rss": '<path d="M5 19.5v.01"/><path d="M4.5 12.5a7 7 0 0 1 7 7"/><path d="M4.5 5.5a14 14 0 0 1 14 14"/>',
    "lien": '<path d="M9.5 14.5a4.2 4.2 0 0 0 6 0l3-3a4.24 4.24 0 0 0-6-6l-1 1"/><path d="M14.5 9.5a4.2 4.2 0 0 0-6 0l-3 3a4.24 4.24 0 0 0 6 6l1-1"/>',
    "haut": '<path d="M12 19V5"/><path d="m6 11 6-6 6 6"/>',
}


def icon(name, size=20, css="icon", stroke=1.6):
    """Retourne un <svg> en ligne ; chaîne vide si le nom est inconnu."""
    body = _PATHS.get(name)
    if not body:
        return ""
    return (
        f'<svg class="{css}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        f'focusable="false">{body}</svg>'
    )


def names():
    return sorted(_PATHS)
