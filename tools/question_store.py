#!/usr/bin/env python3
"""保研skill — 面试题存储管理工具

管理生成的面试题，支持保存、列出、删除、导出操作。
题目以 JSON 格式存储在 data/questions/index.json 中。

用法:
  python question_store.py --action save --file <path> --session <name>
  python question_store.py --action list [--session <name>]
  python question_store.py --action delete --session <name> --id <question_id>
  python question_store.py --action export --session <name> --format json|md
  python question_store.py --action sessions  # 列出所有会话

存储结构:
  data/questions/index.json:
  {
    "sessions": {
      "<session_name>": {
        "created_at": "ISO时间",
        "source_resume": "简历文件名",
        "questions": [
          {
            "id": "q001",
            "category": "technical|behavioral|general",
            "language": "cn|en",
            "question": "问题内容",
            "purpose": "考察目的",
            "hint": "回答提示",
            "follow_ups": ["追问1", "追问2"]
          }
        ]
      }
    }
  }
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 默认数据目录（相对于 skill 根目录）
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DATA_DIR = SKILL_DIR / "data" / "questions"
INDEX_FILE = DATA_DIR / "index.json"


def ensure_data_dir():
    """确保数据目录和索引文件存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text(json.dumps({"sessions": {}}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index():
    """加载索引"""
    ensure_data_dir()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(data):
    """保存索引"""
    ensure_data_dir()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def action_save(file_path, session_name):
    """保存问题到题库"""
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 简单解析 markdown 中的问题
    questions = []
    current_q = None

    lines = content.splitlines()
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()

        # 检测问题标题：### Q1. 或 ### Q1：
        if line.startswith("### Q") or line.startswith("### **Q"):
            if current_q and current_q.get("question"):
                questions.append(current_q)
            current_q = {
                "id": f"q{len(questions) + 1:03d}",
                "question": line.lstrip("# ").strip(),
                "category": "general",
                "language": "en" if "English" in content[:200] or file_path.endswith("_en.md") else "cn",
                "purpose": "",
                "hint": "",
                "follow_ups": [],
            }
        elif current_q:
            if "类别" in line or "Category" in line or "**类别**" in line or "**Category**" in line:
                cat = line.split("：")[-1].split(":")[-1].strip().lower()
                if "技术" in cat or "technical" in cat:
                    current_q["category"] = "technical"
                elif "行为" in cat or "behavioral" in cat:
                    current_q["category"] = "behavioral"
                else:
                    current_q["category"] = "general"
            elif "考察目的" in line or "What I'm assessing" in line:
                current_q["purpose"] = line.split("：")[-1].split(":")[-1].strip()
            elif "参考回答" in line or "Key points" in line:
                current_q["hint"] = line.split("：")[-1].split(":")[-1].strip()
            elif "追问" in line or "follow-up" in line.lower() or "Possible follow" in line:
                pass  # follow_ups handled below
            elif line.startswith("- ") and idx > 0 and "追问" in lines[idx - 1]:
                current_q["follow_ups"].append(line.lstrip("- ").strip())
            elif line.startswith("- "):
                # Check if previous line contained "follow-up" context
                prev_idx = idx - 1
                if prev_idx > 0:
                    prev_line = lines[prev_idx]
                    if "追问" in prev_line or "follow-up" in prev_line.lower() or "Possible follow" in prev_line:
                        current_q["follow_ups"].append(line.lstrip("- ").strip())

    if current_q and current_q.get("question"):
        questions.append(current_q)

    if not questions:
        print("[警告] 未在文件中解析到面试题，将保存原始内容作为备注")
        questions = []

    # 加载现有索引
    index = load_index()

    # 添加新会话
    index["sessions"][session_name] = {
        "created_at": datetime.now().isoformat(),
        "source_file": os.path.basename(file_path),
        "question_count": len(questions),
        "questions": questions,
    }

    save_index(index)
    print(f"[完成] 已保存 {len(questions)} 道题目到会话 '{session_name}'")
    print(f"       数据文件: {INDEX_FILE}")


def action_list(session_name=None):
    """列出问题"""
    index = load_index()
    sessions = index.get("sessions", {})

    if not sessions:
        print("[提示] 题库为空，请先生成面试题。")
        return

    if session_name:
        if session_name not in sessions:
            print(f"[错误] 会话 '{session_name}' 不存在")
            print(f"        可用会话: {', '.join(sessions.keys())}")
            sys.exit(1)

        session = sessions[session_name]
        print(f"\n{'='*60}")
        print(f"会话: {session_name}")
        print(f"创建时间: {session['created_at']}")
        print(f"来源文件: {session.get('source_file', 'N/A')}")
        print(f"题目数量: {session.get('question_count', len(session.get('questions', [])))}")
        print(f"{'='*60}\n")

        for q in session.get("questions", []):
            cat_tag = {"technical": "🔧", "behavioral": "🤝", "general": "📋"}.get(q["category"], "❓")
            lang_tag = "🇨🇳" if q.get("language") == "cn" else "🇬🇧"
            print(f"{cat_tag} {lang_tag} [{q['id']}] {q['question'][:80]}{'...' if len(q.get('question', '')) > 80 else ''}")
            if q.get("purpose"):
                print(f"         考察: {q['purpose'][:60]}")
            print()
    else:
        print("\n📚 题库会话列表:\n")
        for name, session in sessions.items():
            count = session.get("question_count", len(session.get("questions", [])))
            print(f"  📝 {name} — {count} 题 ({session['created_at'][:10]})")
        print(f"\n使用 --session <name> 查看具体题目")


def action_delete(session_name, question_id=None):
    """删除会话或单个问题"""
    index = load_index()
    sessions = index.get("sessions", {})

    if session_name not in sessions:
        print(f"[错误] 会话 '{session_name}' 不存在")
        sys.exit(1)

    if question_id:
        # 删除单个问题
        questions = sessions[session_name].get("questions", [])
        original_count = len(questions)
        questions = [q for q in questions if q["id"] != question_id]
        if len(questions) == original_count:
            print(f"[错误] 未找到题目 '{question_id}'")
            sys.exit(1)
        sessions[session_name]["questions"] = questions
        sessions[session_name]["question_count"] = len(questions)
        print(f"[完成] 已删除题目 '{question_id}'")
    else:
        # 删除整个会话
        del sessions[session_name]
        print(f"[完成] 已删除会话 '{session_name}'")

    index["sessions"] = sessions
    save_index(index)


def action_export(session_name, fmt="json"):
    """导出问题"""
    index = load_index()
    sessions = index.get("sessions", {})

    if session_name not in sessions:
        print(f"[错误] 会话 '{session_name}' 不存在")
        sys.exit(1)

    session = sessions[session_name]

    if fmt == "json":
        output_path = DATA_DIR / f"export_{session_name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
        print(f"[完成] 已导出到: {output_path}")

    elif fmt == "md":
        output_path = DATA_DIR / f"export_{session_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# 面试题 — {session_name}\n\n")
            f.write(f"生成时间：{session['created_at']}\n\n---\n\n")
            for q in session.get("questions", []):
                f.write(f"## {q['id']}. {q['question']}\n\n")
                f.write(f"- **类别**：{q['category']}\n")
                if q.get("purpose"):
                    f.write(f"- **考察目的**：{q['purpose']}\n")
                if q.get("hint"):
                    f.write(f"- **回答提示**：{q['hint']}\n")
                if q.get("follow_ups"):
                    f.write(f"- **可能追问**：\n")
                    for fu in q["follow_ups"]:
                        f.write(f"  - {fu}\n")
                f.write("\n---\n\n")
        print(f"[完成] 已导出到: {output_path}")


def action_sessions():
    """列出所有会话名称"""
    index = load_index()
    sessions = index.get("sessions", {})
    if not sessions:
        print("[提示] 题库为空")
    else:
        for name in sessions:
            print(name)


def main():
    parser = argparse.ArgumentParser(description="保研skill — 面试题存储管理")
    parser.add_argument("--action", required=True,
                        choices=["save", "list", "delete", "export", "sessions"],
                        help="操作类型")
    parser.add_argument("--file", help="要导入的 Markdown 文件路径 (action=save 时必填)")
    parser.add_argument("--session", help="会话名称 (如: 上交2026、北大夏令营)")
    parser.add_argument("--id", help="要删除的问题 ID (action=delete 时可选)")
    parser.add_argument("--format", default="json", choices=["json", "md"],
                        help="导出格式 (action=export 时使用)")
    parser.add_argument("--data-dir", help="数据目录（覆盖默认）")

    args = parser.parse_args()

    global DATA_DIR, INDEX_FILE
    if args.data_dir:
        DATA_DIR = Path(args.data_dir)
        INDEX_FILE = DATA_DIR / "index.json"

    if args.action == "save":
        if not args.file or not args.session:
            print("[错误] --action save 需要 --file 和 --session 参数")
            sys.exit(1)
        action_save(args.file, args.session)

    elif args.action == "list":
        action_list(args.session)

    elif args.action == "delete":
        if not args.session:
            print("[错误] --action delete 需要 --session 参数")
            sys.exit(1)
        action_delete(args.session, args.id)

    elif args.action == "export":
        if not args.session:
            print("[错误] --action export 需要 --session 参数")
            sys.exit(1)
        action_export(args.session, args.format)

    elif args.action == "sessions":
        action_sessions()


if __name__ == "__main__":
    main()
