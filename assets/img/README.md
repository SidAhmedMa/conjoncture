# Images

## Logotypes

Déposez ici vos fichiers de marque ; le générateur les détecte automatiquement
et remplace les substituts en CSS :

| Fichier              | Usage                              | Taille conseillée |
|----------------------|------------------------------------|-------------------|
| `logo-mark.png`      | Pastille ronde (en-tête, pied)     | 176 × 176 px      |
| `logo-wordmark.png`  | Logotype « THE CONJONCTURE REVIEW »| hauteur 88 px     |

Sans ces fichiers, le site affiche un substitut typographique (pastille « TCR »
et logotype composé dans la police d'affichage).

## Visuels d'articles

Placez les images d'article dans `articles/`, puis référencez-les depuis
l'en-tête du fichier Markdown :

    image: "/assets/img/articles/el-aouj.jpg"
    image_alt: "Vue du site minier au crépuscule"
    image_credit: "© Photographe"

Format conseillé : JPEG, 2000 px de large, ratio 16/10 ou 21/9, moins de 400 Ko.
Un article sans image reçoit un repère graphique aux couleurs de sa rubrique.
