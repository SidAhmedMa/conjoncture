#!/usr/bin/env bash
# Bascule le site vers un domaine personnalisé sur GitHub Pages.
#
#   ./tools/domaine.sh theconjoncturereview.com
#
# À lancer une fois le domaine enregistré ET les enregistrements DNS créés.
# Le script vérifie le DNS avant d'agir, puis publie, déclare le domaine et
# active HTTPS dès que le certificat est délivré.

set -euo pipefail

DOMAIN="${1:-}"
REPO="${2:-SidAhmedMa/conjoncture}"
GH_IPS=(185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153)

[ -n "$DOMAIN" ] || { echo "usage: $0 <domaine> [dépôt]" >&2; exit 1; }

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

say "1/5 · Vérification DNS de $DOMAIN"
resolved=$(dig +short "$DOMAIN" A | sort)
if [ -z "$resolved" ]; then
  echo "  ✗ Le domaine ne résout vers aucune adresse."
  echo "    Créez les enregistrements A puis relancez (propagation : 5 min à 24 h)."
  exit 1
fi
echo "  résolu vers :"; echo "$resolved" | sed 's/^/    /'
matched=0
for ip in $resolved; do
  for gh in "${GH_IPS[@]}"; do [ "$ip" = "$gh" ] && matched=$((matched+1)); done
done
if [ "$matched" -eq 0 ]; then
  echo "  ✗ Aucune adresse GitHub Pages parmi les réponses. Attendues :"
  printf '    %s\n' "${GH_IPS[@]}"
  exit 1
fi
echo "  ✓ $matched enregistrement(s) GitHub Pages détecté(s)"

say "2/5 · Déclaration du domaine dans le dépôt"
echo "$DOMAIN" > CNAME
if git diff --quiet --exit-code CNAME 2>/dev/null && git ls-files --error-unmatch CNAME >/dev/null 2>&1; then
  echo "  CNAME déjà à jour"
else
  git add CNAME
  git commit -qm "Domaine personnalisé : $DOMAIN

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
  git push -q origin main
  echo "  ✓ CNAME poussé — le workflow reconstruit pour la racine du domaine"
fi

say "3/5 · Enregistrement du domaine auprès de GitHub Pages"
gh api -X PUT "repos/$REPO/pages" -f "cname=$DOMAIN" -F https_enforced=false >/dev/null 2>&1 \
  && echo "  ✓ domaine déclaré" || echo "  (déjà déclaré, ou à confirmer dans Settings → Pages)"

say "4/5 · Attente du certificat TLS (jusqu'à 15 min)"
for i in $(seq 1 30); do
  state=$(gh api "repos/$REPO/pages" --jq '.https_certificate.state // "en_attente"' 2>/dev/null || echo inconnu)
  printf '\r  état : %-28s (%d/30)' "$state" "$i"
  [ "$state" = "approved" ] && break
  sleep 30
done
echo

say "5/5 · Activation de HTTPS"
if gh api -X PUT "repos/$REPO/pages" -F https_enforced=true >/dev/null 2>&1; then
  echo "  ✓ HTTPS forcé"
else
  echo "  ✗ Certificat pas encore prêt — relancez le script dans quelques minutes."
fi

say "Vérification finale"
for path in / /a-propos/ /flux.xml; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://$DOMAIN$path" || echo "---")
  printf '  %s  https://%s%s\n' "$code" "$DOMAIN" "$path"
done
echo
echo "Site en ligne : https://$DOMAIN/"
