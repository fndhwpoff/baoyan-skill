#!/usr/bin/env python3
"""保研skill — MD转HTML/PDF工具

将 Markdown 文件转换为格式良好的 HTML 文件。
用户可通过浏览器打开 HTML 并打印为 PDF（Ctrl+P）。

用法:
  python pdf_generator.py                    # 全部转换
  python pdf_generator.py --file output/ps/ps_xxx.md
  python pdf_generator.py --category resume
"""

import argparse, os, sys
from pathlib import Path
import markdown

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
OUTPUT_DIR = SKILL_DIR / "output"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 13pt; line-height: 1.9; color: #1a1a2e; max-width: 780px; margin: 40px auto; padding: 20px; }}
h1 {{ font-size: 1.6em; border-bottom: 3px solid #4f46e5; padding-bottom: 10px; margin-top: 0; }}
h2 {{ font-size: 1.3em; margin-top: 1.5em; color: #312e81; }}
h3 {{ font-size: 1.1em; margin-top: 1.2em; }}
table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 11pt; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px 12px; text-align: left; }}
th {{ background: #f3f4f6; font-weight: 700; }}
code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
pre {{ background: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; font-size: 0.9em; border: 1px solid #e5e7eb; }}
strong {{ color: #1f2937; }}
blockquote {{ border-left: 4px solid #4f46e5; padding: 4px 18px; margin: 14px 0; background: #f8fafc; color: #4b5563; }}
hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }}
.toolbar {{ position: fixed; top: 12px; right: 12px; z-index: 999; }}
.toolbar button {{ background: #4f46e5; color: #fff; border: none; padding: 8px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.toolbar button:hover {{ background: #4338ca; }}
@media print {{ body {{ margin: 0; padding: 15px; font-size: 11pt; }} .toolbar {{ display: none; }} }}
</style>
</head>
<body>
<div class="toolbar"><button onclick="window.print()">Print / Save as PDF</button></div>
{body}
</body>
</html>"""


def md_to_html(md_path, html_path=None):
    """转换单个 MD 文件为 HTML"""
    md_path = Path(md_path)
    if not md_path.exists():
        print(f"  [SKIP] not found: {md_path}")
        return False

    if html_path is None:
        html_path = md_path.with_suffix(".html")

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
        html = HTML_TEMPLATE.format(title=md_path.stem, body=body)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"  [OK] {md_path.name} -> {html_path.name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {md_path.name}: {e}")
        return False


def convert_all(category=None):
    cats = ["resume", "questions", "ps", "email", "recommend", "exam", "compare"]
    if category:
        cats = [c for c in cats if c == category]
        if not cats:
            print(f"[ERROR] Unknown category: {category}")
            return

    total, ok = 0, 0
    for cat in cats:
        cat_dir = OUTPUT_DIR / cat
        if not cat_dir.exists():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            if md_file.name == ".gitkeep":
                continue
            total += 1
            if md_to_html(md_file):
                ok += 1

    print(f"\nDone: {ok}/{total} converted")


def main():
    parser = argparse.ArgumentParser(description="MD -> HTML converter")
    parser.add_argument("--file", default=None)
    parser.add_argument("--category", default=None)
    args = parser.parse_args()

    if args.file:
        md_to_html(args.file)
    else:
        convert_all(args.category)


if __name__ == "__main__":
    main()
