# Images

## Logotypes

Déposez vos fichiers de marque ici : le générateur les détecte au moment de la
construction et remplace les substituts composés en CSS. **SVG de préférence**
(net à toutes les tailles) ; PNG, WebP et JPEG sont également acceptés.

### Option A — un seul fichier (recommandé)

| Fichier | Usage |
|---|---|
| `logo-lockup.svg` | verrouillage complet : pastille + logotype + accroche |

C'est le visuel horizontal complet. Il s'affiche dans l'en-tête et dans le pied
de page. Un logo **monochrome foncé sur fond transparent** est éclairci
automatiquement sur les fonds sombres — inutile de fournir une seconde version.

Ajoutez `logo-lockup-light.svg` seulement si vous disposez d'une version claire
dessinée pour les fonds sombres : elle remplacera alors l'inversion automatique.

### Option B — logotype seul

| Fichier | Usage |
|---|---|
| `logo-wordmark.svg` | logotype « THE CONJONCTURE REVIEW » |
| `logo-wordmark-light.svg` | *(facultatif)* version claire pour fonds sombres |

C'est la configuration actuelle du site : le logotype occupe l'en-tête, suivi
d'un filet vertical et de l'accroche composée en texte. Le pied de page utilise
la version claire.

### Option C — éléments séparés

| Fichier | Usage | Taille conseillée |
|---|---|---|
| `logo-mark.png` | pastille ronde seule | 176 × 176 px |
| `logo-wordmark.png` | logotype « THE CONJONCTURE REVIEW » | hauteur 88 px |

Utilisés uniquement si `logo-lockup.*` est absent. L'accroche est alors composée
en texte, à partir de `tagline` dans `site.json`.

> **Fond transparent indispensable.** Un PNG à fond blanc apparaîtra comme un
> rectangle blanc en thème sombre, et l'éclaircissement automatique le rendra
> illisible.

## Visuels d'articles

Placez les images d'article dans `articles/`, puis référencez-les depuis
l'en-tête du fichier Markdown :

    image: "/assets/img/articles/el-aouj.jpg"
    image_alt: "Vue du site minier au crépuscule"
    image_credit: "© Photographe"

Format conseillé : JPEG, 2000 px de large, ratio 16/10 ou 21/9, moins de 400 Ko.
Un article sans image reçoit un repère graphique aux couleurs de sa rubrique.


## Préparer un logo livré sur fond blanc

`tools/prepare_logo.py` recadre au plus juste, remplace le fond blanc par de la
transparence en dérivant l'alpha de la luminance, et produit les deux versions
(foncée et claire) en une passe :

```bash
python3 tools/prepare_logo.py ~/Downloads/logo.png assets/img/logo-wordmark 1200
```

Le dernier argument est la largeur cible en pixels. L'outil détecte la couleur
d'encre et l'affiche : c'est celle sur laquelle la palette du site est alignée
(`--navy-800` dans `assets/css/tcr.css`).

> Inutile si votre logo est déjà un SVG à fond transparent : déposez-le
> directement.
