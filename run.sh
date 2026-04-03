#!/bin/bash
# Quarterly Report — събира данни и публикува dashboard
# Използване: ./run.sh [месеци]

set -e
cd "$(dirname "$0")"

# Зарежда .env
[ -f "$HOME/.env" ] && export $(grep -v '^#' "$HOME/.env" | sed 's/^export //' | xargs)

python3 collect_data.py ${1:-3}

cp output/data.json docs/data.json

git add docs/data.json docs/index.html
git commit -m "data: update $(date '+%Y-%m-%d')" 2>/dev/null || true
git push
