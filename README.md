# The Conjoncture Review

Site de la revue — *Insights on Energy, Infrastructure and Economy*.

Générateur de site statique écrit en Python, **sans aucune dépendance** :
bibliothèque standard uniquement (Python 3.11 ou plus récent). Les articles
s'écrivent en Markdown ; une commande produit un site HTML complet, prêt à
héberger n'importe où.

---

## Démarrage

```bash
python3 build.py --serve --watch
```

Le site est construit dans `dist/`, servi sur <http://localhost:8000> et
reconstruit automatiquement à chaque modification d'un fichier.

| Commande | Effet |
|---|---|
| `python3 build.py` | construit le site dans `dist/` |
| `python3 build.py --serve` | construit puis sert le résultat |
| `python3 build.py --serve --watch` | ajoute la reconstruction automatique |
| `python3 build.py --serve --port 3000` | change le port |
| `python3 build.py --drafts` | inclut les brouillons (`draft: true`) |
| `python3 build.py new "Titre" -r energie` | crée un article pré-rempli |

---

## Écrire un article

```bash
python3 build.py new "Hydrogène vert : le calendrier des projets" -r energie
```

La commande crée `content/energie/2026-08-28-hydrogene-vert-le-calendrier-des-projets.md`
avec un en-tête complet. Rédigez, puis retirez `draft: true` pour publier.

### En-tête du fichier

```yaml
---
title: "Projet El Aouj : prise de la décision finale d'investissement (FID)"
rubrique: mines-industrie          # facultatif : déduit du dossier
date: 2026-07-30
chapeau: "Une étape majeure qui marque l'entrée du plus grand projet minier."
auteur: "Rédaction TCR"
portee: "Mauritanie & International"
tags: [fer, projets miniers, investissement]
image: "/assets/img/articles/el-aouj.jpg"
image_alt: "Vue du site minier au crépuscule"
image_credit: "© Photographe"
lecture: 6                          # facultatif : calculé automatiquement
a_la_une: true                      # place l'article en une de l'accueil
draft: false
---
```

Seul `title` est obligatoire. La date se déduit aussi du nom de fichier, le
temps de lecture du nombre de mots, et l'URL du nom de fichier — soit
`/mines-industrie/el-aouj-decision-finale-investissement/`.

### Rubriques

| Dossier | Rubrique |
|---|---|
| `content/economie/` | Économie |
| `content/energie/` | Énergie |
| `content/infrastructures/` | Infrastructures |
| `content/mines-industrie/` | Mines & Industrie |
| `content/tcr-insights/` | TCR Insights |
| `content/pages/` | pages fixes (à propos, contact, mentions légales) |

---

## Blocs éditoriaux

En plus du Markdown courant (titres, gras, listes, liens, images, tableaux,
citations, code), quatre blocs propres à la revue :

### Chiffres clés

```
::: chiffres "Repères du projet"
2,5 Md$ | Investissement total
12 Mt/an | Capacité à terme
2029 | Première production
:::
```

### L'essentiel

```
::: essentiel
- La décision finale d'investissement est actée.
- Le financement est bouclé.
:::
```

### Citation détachée

```
::: citation "Nom, fonction"
Le calendrier reste le premier facteur de risque.
:::
```

### Encadré et alerte

```
::: encadre "Méthodologie"
Données consolidées au 30 juillet 2026.
:::

::: alerte "À vérifier"
Chiffre en attente de confirmation.
:::
```

> Les espaces insécables de la typographie française (avant `: ; ! ? %` et
> autour des guillemets) sont ajoutées automatiquement, dans le corps de texte
> comme dans les titres.

---

## Configurer le site

Tout se règle dans `site.json` : titre, accroche, URL de production, adresse de
contact, réseaux sociaux, liens de pied de page, nombre d'articles par page — et
la définition des cinq rubriques (nom, mots-clés, description, couleur d'accent,
pictogramme).

Pour brancher la lettre d'information, renseignez l'URL de votre prestataire :

```json
"newsletter_action": "https://votre-service.com/subscribe"
```

Tant que ce champ vaut `#`, le formulaire affiche un message d'aide au lieu
d'envoyer les données.

### Logos

Déposez `logo-mark.png` et `logo-wordmark.png` dans `assets/img/` : ils
remplacent automatiquement les substituts typographiques. Voir
[assets/img/README.md](assets/img/README.md).

### Polices

Le site charge **Syncopate** (affichage) et **Nunito** (texte) depuis Google
Fonts. Pour utiliser la police exacte de votre identité, déposez-la dans
`assets/fonts/`, déclarez-la en `@font-face` en tête de `assets/css/tcr.css`,
puis changez la variable `--font-display`.

---

## Déployer

Le dossier `dist/` est un site statique complet : il se publie tel quel.

- **Netlify** — `netlify.toml` est fourni ; commande `python3 build.py`,
  répertoire publié `dist`.
- **GitHub Pages** — `.github/workflows/deploy.yml` construit et publie à chaque
  poussée sur `main`. Activez Pages en mode « GitHub Actions » dans les réglages
  du dépôt.
- **Hébergement classique** — `python3 build.py`, puis transférez `dist/`.

Avant la mise en ligne, ajustez `"url"` dans `site.json` : cette valeur alimente
les liens canoniques, le flux RSS, le sitemap et les métadonnées de partage.
Pour un déploiement dans un sous-répertoire, renseignez `"base": "/sous-dossier"`.

---

## Ce qui est généré

```
dist/
├── index.html                     accueil (une, dernières publications, fil, rubriques)
├── economie/…                     une page par rubrique, paginée au-delà de 12 articles
│   └── mon-article/index.html     page d'article
├── archives/                      toutes les publications, filtrables par rubrique
├── recherche/
│   ├── index.html                 recherche côté client
│   └── index.json                 index de recherche
├── a-propos/  contact/  mentions-legales/
├── 404.html   flux.xml   sitemap.xml   robots.txt
└── assets/
```

Inclus par défaut : thème clair et sombre, recherche instantanée insensible aux
accents (`Ctrl/⌘ + K` ou `/`), sommaire d'article avec suivi de lecture, boutons
de partage, flux RSS, données structurées `NewsArticle`, métadonnées Open Graph,
et une hiérarchie de titres vérifiée sur chaque page.

---

## Organisation du code

```
build.py              interface en ligne de commande (build, serve, watch, new)
site.json             configuration du site et des rubriques
tcr/
  config.py           chargement de la configuration, dates en français
  frontmatter.py      lecture des en-têtes de fichiers
  markdown.py         conversion Markdown + blocs éditoriaux + typographie
  content.py          modèle d'article, tri, articles liés
  templates.py        moteur de gabarits ({{ variable }}, {{#if}})
  render.py           composants et assemblage des pages
  icons.py            pictogrammes SVG
  feeds.py            RSS, sitemap, robots, index de recherche
templates/            gabarits HTML modifiables
assets/               CSS, JavaScript, images, polices
content/              vos articles
```

---

## Contenu de démonstration

Les onze articles livrés servent à valider la mise en page. Chacun s'ouvre sur
un bloc « Contenu de démonstration » : ce ne sont pas des articles réels.
Supprimez-les avant la mise en ligne.

```bash
rm content/*/20*.md
```
