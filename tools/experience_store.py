#!/usr/bin/env python3
"""保研skill — 面试经验库管理

保存和管理各校机械工程保研面试经验（面经）。

用法:
  python experience_store.py --action save --school 上交 --year 2026 --data '<json>'
  python experience_store.py --action list --school 上交
  python experience_store.py --action search --keyword 机械原理
  python experience_store.py --action delete --school 上交 --year 2026
  python experience_store.py --action export --school 上交 --format md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DATA_DIR = SKILL_DIR / "data" / "experiences"
INDEX_FILE = DATA_DIR / "index.json"


def load_data():
    """加载经验库"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"experiences": {}, "updated_at": None}


def save_data(data):
    """保存经验库"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def action_save(school, year, data_json):
    """保存面试经验"""
    try:
        entry = json.loads(data_json)
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 解析失败: {e}")
        sys.exit(1)

    data = load_data()
    key = f"{school}_{year}"

    existing = data["experiences"].get(key, {})
    existing.update(entry)
    existing.setdefault("school", school)
    existing.setdefault("year", year)
    existing["saved_at"] = datetime.now().isoformat()

    data["experiences"][key] = existing
    save_data(data)
    print(f"[已保存] {school} ({year}) — 面试经验")


def action_list(school=None, keyword=None):
    """列出面试经验"""
    data = load_data()
    experiences = data.get("experiences", {})

    if school:
        experiences = {k: v for k, v in experiences.items() if v.get("school") == school}
    if keyword:
        def has_keyword(exp):
            text = json.dumps(exp, ensure_ascii=False).lower()
            return keyword.lower() in text
        experiences = {k: v for k, v in experiences.items() if has_keyword(v)}

    if not experiences:
        print("[空] 没有匹配的面试经验")
        return

    print(f"\n{'='*60}")
    print(f"保研面试经验库 — {len(experiences)} 条记录")
    print(f"{'='*60}")

    for key, exp in sorted(experiences.items()):
        school_name = exp.get("school", key.split("_")[0])
        year = exp.get("year", "?")
        program = exp.get("program", "?")
        fmt = exp.get("format", "?")
        diff = exp.get("difficulty_rating", "?")
        source_count = len(exp.get("source_urls", []))

        print(f"\n[{school_name}] {year}年 {program} — {fmt}")
        print(f"  难度: {'⭐' * (diff if isinstance(diff, int) else 0) or diff}")
        print(f"  来源: {source_count} 个")
        if exp.get("summary"):
            print(f"  概述: {exp['summary'][:100]}...")
        if exp.get("tips"):
            print(f"  关键建议: {exp['tips'][0][:80]}")
        if exp.get("questions_chinese"):
            print(f"  中文问题数: {len(exp['questions_chinese'])}")
        if exp.get("questions_english"):
            print(f"  英文问题数: {len(exp['questions_english'])}")


def action_delete(school, year):
    """删除面试经验"""
    data = load_data()
    key = f"{school}_{year}"

    if key in data["experiences"]:
        del data["experiences"][key]
        save_data(data)
        print(f"[已删除] {school} ({year})")
    else:
        print(f"[未找到] {school} ({year})")


def action_export(school=None, fmt="json"):
    """导出面试经验"""
    data = load_data()
    experiences = data.get("experiences", {})

    if school:
        experiences = {k: v for k, v in experiences.items() if v.get("school") == school}

    if fmt == "json":
        print(json.dumps(experiences, ensure_ascii=False, indent=2))
    elif fmt == "md":
        print("# 保研面试经验汇总\n")
        for key, exp in sorted(experiences.items()):
            print(f"## {exp.get('school', '?')} ({exp.get('year', '?')}年)")
            print(f"- 项目: {exp.get('program', '?')}")
            print(f"- 形式: {exp.get('format', '?')}")
            print(f"- 难度: {exp.get('difficulty_rating', '?')}/5")
            print(f"\n### 概述\n{exp.get('summary', '无')}")
            if exp.get("questions_chinese"):
                print("\n### 常见中文问题")
                for q in exp["questions_chinese"]:
                    print(f"- {q}")
            if exp.get("questions_english"):
                print("\n### 常见英文问题")
                for q in exp["questions_english"]:
                    print(f"- {q}")
            if exp.get("tips"):
                print("\n### 备考建议")
                for t in exp["tips"]:
                    print(f"- {t}")
            print(f"\n---\n")


def main():
    parser = argparse.ArgumentParser(description="保研skill — 面试经验库管理")
    parser.add_argument("--action", required=True,
                        choices=["save", "list", "delete", "export"],
                        help="操作类型")
    parser.add_argument("--school", default=None,
                        help="学校简称（如 上交/浙大/华科）")
    parser.add_argument("--year", type=int, default=None,
                        help="经验年份")
    parser.add_argument("--data", default=None,
                        help="JSON 数据（save 操作）")
    parser.add_argument("--keyword", default=None,
                        help="关键词搜索（list 操作）")
    parser.add_argument("--format", default="json",
                        choices=["json", "md"],
                        help="导出格式（export 操作）")

    args = parser.parse_args()

    if args.action == "save":
        if not args.school or not args.year or not args.data:
            print("[错误] save 需要 --school, --year, --data 参数")
            sys.exit(1)
        action_save(args.school, args.year, args.data)

    elif args.action == "list":
        action_list(args.school, args.keyword)

    elif args.action == "delete":
        if not args.school or not args.year:
            print("[错误] delete 需要 --school, --year 参数")
            sys.exit(1)
        action_delete(args.school, args.year)

    elif args.action == "export":
        action_export(args.school, args.format)


if __name__ == "__main__":
    main()
