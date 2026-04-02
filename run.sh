#!/bin/bash
# Quarterly Report — събира данни и публикува dashboard
# Използване: ./run.sh [месеци]   (по подразбиране: 3)

set -e
cd "$(dirname "$0")"

python3 collect_data.py ${1:-3}

cp output/data.json docs/data.json

git add docs/data.json
git commit -m "data: update $(date '+%Y-%m-%d')" 2>/dev/null || true
git push
