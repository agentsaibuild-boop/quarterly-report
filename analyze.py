#!/usr/bin/env python3
"""
Стъпка 2: AI анализ на събраните данни.
Изпраща data.json към Claude API (или OpenRouter) и получава честен анализ.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


DATA_FILE = Path(__file__).parent / "output" / "data.json"
ANALYSIS_FILE = Path(__file__).parent / "output" / "analysis.json"

SYSTEM_PROMPT = """Ти си безпристрастен анализатор на продуктивността и финансите на разработчик/малък екип.
Задачата ти е да анализираш данните и да дадеш ЧЕСТНА, РЕАЛНА оценка — без украсяване и без негативизъм.

Форматирай отговора като JSON с тази структура:
{
  "summary": "2-3 изречения обобщение на периода",
  "overall_rating": "висока/средна/ниска продуктивност + едно изречение защо",
  "projects": [
    {
      "name": "...",
      "assessment": "честна оценка за напредъка",
      "red_flags": ["проблеми ако има"],
      "positives": ["постижения ако има"]
    }
  ],
  "expenses_analysis": {
    "verdict": "оценка дали разходите са оправдани спрямо работата",
    "concerns": ["притеснения ако има"],
    "roi_note": "коментар за връзката разходи/резултат"
  },
  "honest_observations": [
    "директни наблюдения — неудобни истини ако има такива"
  ],
  "recommendations": [
    "конкретни препоръки за следващия период"
  ]
}

Отговаряй САМО с валиден JSON. Без markdown, без ```json блокове."""


def call_openrouter(api_key: str, user_message: str) -> str:
    """Извиква OpenRouter API с Claude модел."""
    payload = json.dumps({
        "model": "anthropic/claude-opus-4",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trimesechenReport",
            "X-Title": "TrimesechenReport",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()


def call_anthropic(api_key: str, user_message: str) -> str:
    """Извиква Anthropic API директно."""
    payload = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["content"][0]["text"].strip()


def analyze(data: dict = None) -> dict:
    if data is None:
        if not DATA_FILE.exists():
            print("Грешка: data.json не е намерен. Пусни първо collect_data.py")
            sys.exit(1)
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    # Зарежда .env ако съществува
    env_file = Path.home() / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not openrouter_key and not anthropic_key:
        print("Грешка: OPENROUTER_API_KEY или ANTHROPIC_API_KEY не е зададен")
        sys.exit(1)

    user_message = f"""Анализирай следните данни за период {data['period']['from']} → {data['period']['to']}:

{json.dumps(data, ensure_ascii=False, indent=2)}

Дай честен анализ. Ако някой проект е стагнирал — кажи го. Ако разходите не са оправдани — кажи го."""

    print("Изпращам данни за анализ...")

    try:
        if openrouter_key:
            print("  Използвам OpenRouter API...")
            raw = call_openrouter(openrouter_key, user_message)
        else:
            print("  Използвам Anthropic API...")
            raw = call_anthropic(anthropic_key, user_message)
    except urllib.error.HTTPError as e:
        print(f"HTTP Грешка: {e.code} {e.reason}")
        body = e.read().decode("utf-8")
        print(f"Детайли: {body[:500]}")
        sys.exit(1)

    try:
        # Опит за директен JSON parse
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        # Опит за извличане на JSON от markdown блок
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        if match:
            try:
                analysis = json.loads(match.group(1))
            except json.JSONDecodeError:
                analysis = {"raw_response": raw}
        else:
            analysis = {"raw_response": raw}

    output = {
        "period": data["period"],
        "generated_at": data["generated_at"],
        "analysis": analysis,
    }

    ANALYSIS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Анализът записан в: {ANALYSIS_FILE}")
    return output


if __name__ == "__main__":
    analyze()
