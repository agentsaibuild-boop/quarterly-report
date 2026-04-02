#!/usr/bin/env python3
"""
Стъпка 2: AI анализ на събраните данни.
Изпраща data.json към Claude API и получава честен анализ.
"""

import json
import os
import sys
from pathlib import Path
import anthropic


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


def analyze(data: dict = None) -> dict:
    if data is None:
        if not DATA_FILE.exists():
            print("Грешка: data.json не е намерен. Пусни първо collect_data.py")
            sys.exit(1)
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Грешка: ANTHROPIC_API_KEY не е зададен")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"""Анализирай следните данни за период {data['period']['from']} → {data['period']['to']}:

{json.dumps(data, ensure_ascii=False, indent=2)}

Дай честен анализ. Ако някой проект е стагнирал — кажи го. Ако разходите не са оправдани — кажи го."""

    print("Изпращам данни към Claude за анализ...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        # Ако Claude върне нещо различно, пазим го като текст
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
