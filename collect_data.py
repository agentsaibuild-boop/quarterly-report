#!/usr/bin/env python3
"""
Стъпка 1: Събиране на данни за тримесечния отчет.
Генерира data.json с факти за всички проекти и разходи.
"""

import json
import subprocess
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


CONFIG_FILE = Path(__file__).parent / "config.json"


def get_period(months: int = 3):
    end = datetime.now()
    start = end - timedelta(days=months * 30)
    return start, end


def git_stat(repo_path: str, author: str, since: str, until: str) -> dict:
    """Събира git статистика за даден период."""
    path = Path(repo_path)
    if not (path / ".git").exists():
        return {"error": "не е git репо"}

    def run(cmd):
        try:
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=15
            )
            return result.stdout.strip()
        except Exception as e:
            return ""

    author_filter = ["--author", author] if author else []
    date_filter = [f"--since={since}", f"--until={until}"]

    # Брой commits
    commits_out = run(
        ["git", "log", "--oneline"] + author_filter + date_filter
    )
    commit_lines = [l for l in commits_out.splitlines() if l.strip()]
    commit_count = len(commit_lines)
    commit_messages = [l.split(" ", 1)[1] if " " in l else l for l in commit_lines[:20]]

    # Добавени/изтрити редове
    stat_out = run(
        ["git", "log", "--numstat", "--pretty="] + author_filter + date_filter
    )
    added = 0
    removed = 0
    files_changed = set()
    for line in stat_out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            try:
                added += int(parts[0])
                removed += int(parts[1])
                files_changed.add(parts[2])
            except ValueError:
                pass

    # Последен commit
    last_commit = run(["git", "log", "-1", "--format=%ci %s"])

    # Текущ branch
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    # Общ брой файлове в репото
    total_files = run(["git", "ls-files", "--cached"])
    total_file_count = len(total_files.splitlines()) if total_files else 0

    return {
        "commits_in_period": commit_count,
        "lines_added": added,
        "lines_removed": removed,
        "files_changed_in_period": len(files_changed),
        "total_files_in_repo": total_file_count,
        "last_commit": last_commit,
        "current_branch": branch,
        "recent_commit_messages": commit_messages,
    }


def folder_stat(folder_path: str) -> dict:
    """Статистика за папка без git."""
    path = Path(folder_path)
    if not path.exists():
        return {"error": "папката не съществува"}

    file_count = 0
    total_size = 0
    newest_mtime = 0

    for f in path.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            file_count += 1
            try:
                stat = f.stat()
                total_size += stat.st_size
                if stat.st_mtime > newest_mtime:
                    newest_mtime = stat.st_mtime
            except OSError:
                pass

    newest_date = (
        datetime.fromtimestamp(newest_mtime).isoformat()
        if newest_mtime
        else "неизвестно"
    )

    return {
        "total_files": file_count,
        "total_size_kb": round(total_size / 1024, 1),
        "last_modified": newest_date,
    }


def load_expenses(expenses_file: str, since: datetime, until: datetime) -> dict:
    """Чете разходите от CSV за периода."""
    path = Path(expenses_file)
    if not path.is_absolute():
        path = Path(__file__).parent / expenses_file

    if not path.exists():
        return {"error": f"файл не е намерен: {path}", "rows": [], "total_bgn": 0}

    rows = []
    total = 0.0
    by_category = {}
    by_project = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date = datetime.strptime(row["date"].strip(), "%Y-%m-%d")
            except ValueError:
                continue
            if not (since <= date <= until):
                continue

            amount = float(row.get("amount_bgn", 0))
            category = row.get("category", "друго").strip()
            project = row.get("project", "general").strip()

            rows.append({
                "date": row["date"].strip(),
                "category": category,
                "description": row.get("description", "").strip(),
                "amount_bgn": amount,
                "project": project,
            })
            total += amount
            by_category[category] = by_category.get(category, 0) + amount
            by_project[project] = by_project.get(project, 0) + amount

    return {
        "rows": rows,
        "total_bgn": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "by_project": {k: round(v, 2) for k, v in by_project.items()},
    }


def collect(months: int = None) -> dict:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    months = months or config.get("default_period_months", 3)
    author = config.get("git_author", "")

    since, until = get_period(months)
    since_str = since.strftime("%Y-%m-%d")
    until_str = until.strftime("%Y-%m-%d")

    print(f"Период: {since_str} → {until_str}")
    print(f"Проекти: {len(config['projects'])}")

    projects_data = []
    for proj in config["projects"]:
        name = proj["name"]
        path = proj["path"]
        ptype = proj.get("type", "git")
        print(f"  Обработвам: {name} ({ptype})...")

        if ptype == "git":
            stat = git_stat(path, author, since_str, until_str)
        else:
            stat = folder_stat(path)

        projects_data.append({
            "name": name,
            "description": proj.get("description", ""),
            "type": ptype,
            "path": path,
            "stats": stat,
        })

    expenses = load_expenses(config["expenses_file"], since, until)

    data = {
        "generated_at": datetime.now().isoformat(),
        "period": {
            "from": since_str,
            "to": until_str,
            "months": months,
        },
        "projects": projects_data,
        "expenses": expenses,
    }

    output_dir = Path(__file__).parent / config.get("output_dir", "output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "data.json"
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nДанните записани в: {output_file}")
    return data


if __name__ == "__main__":
    months = int(sys.argv[1]) if len(sys.argv) > 1 else None
    collect(months)
