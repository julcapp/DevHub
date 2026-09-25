from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.workspaces.architecture.analytics import build_markdown, load_records, summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevHub Architecture Trend")
    parser.add_argument("results", nargs="?", default=".", help="Каталог с JSON-результатами Architecture Quality Gate")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Вывести сводку в JSON")
    parser.add_argument("--markdown-output", help="Сохранить Markdown-сводку в файл")
    args = parser.parse_args(argv)

    records = load_records(Path(args.results))
    trend = summarize(records)
    markdown = build_markdown(trend)

    if args.markdown_output:
        output = Path(args.markdown_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")

    if args.as_json:
        print(json.dumps(asdict(trend), ensure_ascii=False, indent=2))
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
