from pathlib import Path


REQUIRED_README_SECTIONS = [
    "описание",
    "назначение",
    "возможности",
    "структура",
    "установка",
    "запуск",
    "roadmap",
    "лицензия"
]


def _read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def analyze_readme(repo_path: Path) -> dict:
    readme = repo_path / "README.md"
    content = _read_file(readme)
    lower_content = content.lower()

    if not content.strip():
        return {
            "score": 0,
            "status": "missing_or_empty",
            "recommendations": [
                "README отсутствует или пустой.",
                "Рекомендуется создать README с описанием назначения, структуры, установки и запуска проекта."
            ]
        }

    missing_sections = [
        section for section in REQUIRED_README_SECTIONS
        if section not in lower_content
    ]

    existing_score = len(REQUIRED_README_SECTIONS) - len(missing_sections)
    score = int((existing_score / len(REQUIRED_README_SECTIONS)) * 100)

    recommendations = []
    if missing_sections:
        recommendations.append(
            "README не полностью описывает проект. Отсутствуют разделы: "
            + ", ".join(missing_sections)
            + "."
        )
    else:
        recommendations.append("README содержит базовые разделы.")

    # Compare README with project folders.
    important_dirs = [
        item.name for item in repo_path.iterdir()
        if item.is_dir()
        and not item.name.startswith(".")
        and item.name.lower() not in {"__pycache__", "node_modules", "venv", "dist", "build"}
    ]

    undocumented_dirs = [
        dirname for dirname in important_dirs
        if dirname.lower() not in lower_content
    ]

    if undocumented_dirs:
        recommendations.append(
            "В проекте есть каталоги, которые не упомянуты в README: "
            + ", ".join(undocumented_dirs[:8])
            + "."
        )

    return {
        "score": score,
        "status": "ok" if score >= 80 else "needs_update",
        "missing_sections": missing_sections,
        "undocumented_dirs": undocumented_dirs,
        "recommendations": recommendations
    }


def build_project_advice(repo_path: Path) -> list[str]:
    lines = []
    readme_result = analyze_readme(repo_path)

    lines.append("DevAdvisor")
    lines.append("")
    lines.append(f"Проект: {repo_path.name}")
    lines.append(f"README Score: {readme_result['score']}%")
    lines.append("")

    for recommendation in readme_result.get("recommendations", []):
        lines.append(f"• {recommendation}")

    dhms_file = repo_path / ".devhub" / "project.json"
    if not dhms_file.exists():
        lines.append("• DHMS-паспорт проекта отсутствует. Рекомендуется создать .devhub/project.json.")

    if (repo_path / "docs").exists() is False:
        lines.append("• Папка docs отсутствует. Рекомендуется добавить документацию проекта.")

    if (repo_path / "CHANGELOG.md").exists() is False:
        lines.append("• CHANGELOG.md отсутствует. Рекомендуется вести историю изменений.")

    return lines
