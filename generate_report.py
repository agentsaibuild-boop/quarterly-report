#!/usr/bin/env python3
"""
Стъпка 3: Генериране на HTML отчет от анализа.
Създава professional HTML файл подходящ за изпращане.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


ANALYSIS_FILE = Path(__file__).parent / "output" / "analysis.json"
DATA_FILE = Path(__file__).parent / "output" / "data.json"
OUTPUT_DIR = Path(__file__).parent / "output"


def badge(text: str, color: str) -> str:
    colors = {
        "green": "#22c55e",
        "red": "#ef4444",
        "orange": "#f97316",
        "blue": "#3b82f6",
        "gray": "#6b7280",
    }
    bg = colors.get(color, colors["gray"])
    return f'<span style="background:{bg};color:white;padding:2px 10px;border-radius:12px;font-size:0.8em;font-weight:600">{text}</span>'


def rating_color(rating_text: str) -> str:
    text = rating_text.lower()
    if "висока" in text:
        return "green"
    if "ниска" in text:
        return "red"
    return "orange"


def generate_html(analysis_data: dict, raw_data: dict) -> str:
    period = analysis_data["period"]
    a = analysis_data["analysis"]

    # Дата на генериране
    gen_date = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Проекти таблица
    projects_rows = ""
    for proj in raw_data["projects"]:
        stats = proj["stats"]
        if proj["type"] == "git":
            commits = stats.get("commits_in_period", 0)
            lines = f"+{stats.get('lines_added', 0)} / -{stats.get('lines_removed', 0)}"
            activity = badge("активен", "green") if commits > 0 else badge("неактивен", "gray")
        else:
            commits = "—"
            lines = f"{stats.get('total_files', '?')} файла"
            last_mod = stats.get("last_modified", "")
            activity = badge("папка", "blue")

        projects_rows += f"""
        <tr>
          <td><strong>{proj['name']}</strong><br><small style="color:#6b7280">{proj['description']}</small></td>
          <td style="text-align:center">{commits}</td>
          <td style="text-align:center">{lines}</td>
          <td>{activity}</td>
        </tr>"""

    # AI анализ по проекти
    projects_analysis = ""
    for proj_a in a.get("projects", []):
        red_flags_html = ""
        if proj_a.get("red_flags"):
            items = "".join(f"<li>{f}</li>" for f in proj_a["red_flags"])
            red_flags_html = f'<div style="margin-top:8px"><strong style="color:#ef4444">⚠ Проблеми:</strong><ul style="margin:4px 0">{items}</ul></div>'

        positives_html = ""
        if proj_a.get("positives"):
            items = "".join(f"<li>{p}</li>" for p in proj_a["positives"])
            positives_html = f'<div style="margin-top:8px"><strong style="color:#22c55e">✓ Постижения:</strong><ul style="margin:4px 0">{items}</ul></div>'

        projects_analysis += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:12px">
          <h3 style="margin:0 0 8px 0;font-size:1em">{proj_a['name']}</h3>
          <p style="margin:0;color:#374151">{proj_a.get('assessment', '')}</p>
          {red_flags_html}
          {positives_html}
        </div>"""

    # Разходи
    expenses = raw_data["expenses"]
    expenses_rows = ""
    for row in expenses.get("rows", []):
        expenses_rows += f"""
        <tr>
          <td>{row['date']}</td>
          <td>{row['category']}</td>
          <td>{row['description']}</td>
          <td style="text-align:right;font-weight:600">{row['amount_bgn']:.2f} лв.</td>
          <td>{row['project']}</td>
        </tr>"""

    by_cat = expenses.get("by_category", {})
    by_cat_rows = "".join(
        f"<tr><td>{k}</td><td style='text-align:right;font-weight:600'>{v:.2f} лв.</td></tr>"
        for k, v in by_cat.items()
    )

    # Наблюдения и препоръки
    observations_html = "".join(
        f"<li>{o}</li>" for o in a.get("honest_observations", [])
    )
    recommendations_html = "".join(
        f"<li>{r}</li>" for r in a.get("recommendations", [])
    )

    exp_analysis = a.get("expenses_analysis", {})
    concerns_html = "".join(
        f"<li>{c}</li>" for c in exp_analysis.get("concerns", [])
    )

    rating_text = a.get("overall_rating", "")
    rating_col = rating_color(rating_text)

    html = f"""<!DOCTYPE html>
<html lang="bg">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Тримесечен отчет {period['from']} – {period['to']}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; color: #111827; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 40px auto; padding: 0 20px 60px; }}
  .header {{ background: #1e293b; color: white; padding: 32px; border-radius: 12px; margin-bottom: 32px; }}
  .header h1 {{ font-size: 1.6em; font-weight: 700; }}
  .header p {{ color: #94a3b8; margin-top: 4px; }}
  .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 1.1em; font-weight: 700; color: #1e293b; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
  th {{ background: #f8fafc; text-align: left; padding: 10px 12px; font-weight: 600; color: #475569; border-bottom: 2px solid #e2e8f0; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
  tr:last-child td {{ border-bottom: none; }}
  .summary-box {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 0 8px 8px 0; }}
  .rating-box {{ display:inline-block; padding: 8px 20px; border-radius: 8px; font-weight: 700; font-size: 0.95em; }}
  .obs-list li {{ padding: 6px 0; border-bottom: 1px solid #f1f5f9; list-style: none; padding-left: 20px; position: relative; }}
  .obs-list li::before {{ content: "→"; position: absolute; left: 0; color: #6b7280; }}
  .rec-list li {{ padding: 6px 0; border-bottom: 1px solid #f1f5f9; list-style: none; padding-left: 20px; position: relative; }}
  .rec-list li::before {{ content: "✓"; position: absolute; left: 0; color: #22c55e; font-weight: 700; }}
  .footer {{ text-align: center; color: #9ca3af; font-size: 0.8em; margin-top: 40px; }}
  .total-row td {{ font-weight: 700; font-size: 1.05em; background: #f8fafc; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Тримесечен отчет</h1>
    <p>Период: {period['from']} → {period['to']} &nbsp;|&nbsp; Генериран: {gen_date}</p>
  </div>

  <!-- ОБОБЩЕНИЕ -->
  <div class="section">
    <h2>Обобщение</h2>
    <div class="summary-box" style="margin-bottom:16px">
      <p>{a.get('summary', '')}</p>
    </div>
    <div>
      <strong>Обща оценка: </strong>
      <span class="rating-box" style="background:{'#dcfce7' if rating_col == 'green' else '#fee2e2' if rating_col == 'red' else '#ffedd5'};color:{'#166534' if rating_col == 'green' else '#991b1b' if rating_col == 'red' else '#9a3412'}">
        {rating_text}
      </span>
    </div>
  </div>

  <!-- ПРОЕКТИ — ДАННИ -->
  <div class="section">
    <h2>Проекти — активност</h2>
    <table>
      <thead>
        <tr>
          <th>Проект</th>
          <th style="text-align:center">Commits</th>
          <th style="text-align:center">Редове</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        {projects_rows}
      </tbody>
    </table>
  </div>

  <!-- ПРОЕКТИ — АНАЛИЗ -->
  <div class="section">
    <h2>Проекти — AI оценка</h2>
    {projects_analysis}
  </div>

  <!-- РАЗХОДИ -->
  <div class="section">
    <h2>Разходи за периода</h2>
    <table>
      <thead>
        <tr>
          <th>Дата</th>
          <th>Категория</th>
          <th>Описание</th>
          <th style="text-align:right">Сума</th>
          <th>Проект</th>
        </tr>
      </thead>
      <tbody>
        {expenses_rows}
        <tr class="total-row">
          <td colspan="3">Общо</td>
          <td style="text-align:right">{expenses.get('total_bgn', 0):.2f} лв.</td>
          <td></td>
        </tr>
      </tbody>
    </table>

    {"<br><table><thead><tr><th>По категория</th><th style='text-align:right'>Сума</th></tr></thead><tbody>" + by_cat_rows + "</tbody></table>" if by_cat else ""}

    <div style="margin-top:20px;padding:16px;background:#fef3c7;border-radius:8px;border-left:4px solid #f59e0b">
      <strong>AI оценка на разходите:</strong>
      <p style="margin-top:8px">{exp_analysis.get('verdict', '')}</p>
      {f'<p style="margin-top:8px;color:#92400e"><em>{exp_analysis.get("roi_note", "")}</em></p>' if exp_analysis.get('roi_note') else ''}
      {f'<ul style="margin-top:8px">{concerns_html}</ul>' if exp_analysis.get('concerns') else ''}
    </div>
  </div>

  <!-- НАБЛЮДЕНИЯ -->
  <div class="section">
    <h2>Честни наблюдения</h2>
    <ul class="obs-list">
      {observations_html}
    </ul>
  </div>

  <!-- ПРЕПОРЪКИ -->
  <div class="section">
    <h2>Препоръки за следващия период</h2>
    <ul class="rec-list">
      {recommendations_html}
    </ul>
  </div>

  <div class="footer">
    Тримесечен отчет | Генериран автоматично | {gen_date}
  </div>

</div>
</body>
</html>"""

    return html


def generate(analysis_data: dict = None, raw_data: dict = None):
    if analysis_data is None:
        if not ANALYSIS_FILE.exists():
            print("Грешка: analysis.json не е намерен. Пусни analyze.py")
            sys.exit(1)
        analysis_data = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))

    if raw_data is None:
        if not DATA_FILE.exists():
            print("Грешка: data.json не е намерен. Пусни collect_data.py")
            sys.exit(1)
        raw_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    OUTPUT_DIR.mkdir(exist_ok=True)
    html = generate_html(analysis_data, raw_data)

    period = analysis_data["period"]
    filename = f"report_{period['from']}_{period['to']}.html"
    out_path = OUTPUT_DIR / filename

    out_path.write_text(html, encoding="utf-8")
    print(f"Отчетът генериран: {out_path}")
    return out_path


if __name__ == "__main__":
    generate()
