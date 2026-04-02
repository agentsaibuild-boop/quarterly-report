#!/bin/bash
# Тримесечен отчет — главен runner
# Използване: ./run.sh [месеци]
# Пример:     ./run.sh 3

set -e
cd "$(dirname "$0")"

MONTHS=${1:-3}

echo "=== Тримесечен отчет ==="
echo "Период: последните $MONTHS месеца"
echo ""

# Проверка за ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ГРЕШКА: ANTHROPIC_API_KEY не е зададен"
  echo "Създай .env файл или export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

# Проверка за Python зависимости
python3 -c "import anthropic" 2>/dev/null || {
  echo "Инсталирам anthropic..."
  pip3 install anthropic --quiet
}

echo "[1/3] Събиране на данни..."
python3 collect_data.py $MONTHS

echo ""
echo "[2/3] AI анализ..."
python3 analyze.py

echo ""
echo "[3/3] Генериране на HTML отчет..."
python3 generate_report.py

echo ""
echo "=== Готово! ==="
echo "Отчетът е в папка: output/"
ls -la output/*.html 2>/dev/null || true
