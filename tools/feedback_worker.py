#!/usr/bin/env python3
"""保研skill — 反馈处理工具

监控 feedback 目录，自动处理待处理的反馈请求。
支持一次性批处理模式和持续监控模式。

用法:
  python feedback_worker.py              # 处理所有待处理反馈后退出
  python feedback_worker.py --watch      # 持续监控，自动处理新请求
"""

import argparse, json, os, sys, time
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
FEEDBACK_DIR = SKILL_DIR / "data" / "feedback"


def process_pending():
    """处理所有待处理的反馈请求"""
    if not FEEDBACK_DIR.exists():
        print("[信息] 反馈目录不存在，无待处理请求")
        return 0

    pending = sorted(FEEDBACK_DIR.glob("feedback_*.json"))
    count = 0
    for f in pending:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # 跳过已处理的
            if data.get("feedback") is not None:
                continue
            # 基于规则生成反馈（后续可替换为AI调用）
            result = evaluate_answer(data.get("question", ""), data.get("transcript", ""), data.get("category", "general"))
            data["feedback"] = result
            data["processed_at"] = datetime.now().isoformat()
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            count += 1
            print(f"  [已处理] {f.name}")
        except Exception as e:
            print(f"  [错误] {f.name}: {e}")
    return count


def evaluate_answer(question, transcript, category):
    """基于规则评估回答质量"""
    if not transcript or len(transcript) < 10:
        return {
            "scores": {"content": 3, "fluency": 3, "logic": 3},
            "overall": 3.0,
            "strengths": [],
            "suggestions": ["回答内容过短，建议至少用3-5句话展开你的观点。"]
        }

    word_count = len(transcript.split())
    char_count = len(transcript)

    # 内容质量：基于长度和关键词
    content_score = min(10, max(3, 4 + word_count / 30))
    if category == "technical":
        tech_keywords = ["方法", "结果", "分析", "数据", "实验", "模型", "设计", "算法", "优化"]
        hits = sum(1 for kw in tech_keywords if kw in transcript)
        content_score = min(10, content_score + hits * 0.5)

    # 流利度：基于句子长度分布
    sentences = [s.strip() for s in transcript.replace("!", ".").replace("？", ".").split(".") if s.strip()]
    avg_len = sum(len(s) for s in sentences) / max(1, len(sentences))
    fluency_score = min(10, max(3, 5 + (20 - abs(avg_len - 80)) / 20))

    # 逻辑结构
    logic_score = min(10, max(3, 4 + len(sentences) / 3))
    if any(kw in transcript for kw in ["首先", "其次", "最后", "第一", "第二", "因为", "所以", "因此"]):
        logic_score = min(10, logic_score + 2)
    if any(kw in transcript.lower() for kw in ["first", "second", "finally", "because", "therefore"]):
        logic_score = min(10, logic_score + 2)

    overall = round((content_score + fluency_score + logic_score) / 3, 1)

    strengths = []
    suggestions = []
    if content_score >= 7:
        strengths.append("内容详实，对你的项目有深入的理解")
    else:
        suggestions.append("建议用更多具体数据和细节来支撑你的观点")
    if fluency_score >= 7:
        strengths.append("表达流畅，语言组织能力好")
    else:
        suggestions.append("尝试用更自然的语速和停顿来提升表达流畅度")
    if logic_score >= 7:
        strengths.append("回答逻辑清晰，结构分明")
    else:
        suggestions.append("建议采用'总-分-总'结构：先给结论→展开论述→总结要点")

    return {
        "scores": {"content": round(content_score), "fluency": round(fluency_score), "logic": round(logic_score)},
        "overall": overall,
        "strengths": strengths,
        "suggestions": suggestions,
    }


def watch_mode():
    """持续监控模式"""
    print(f"[监控] 开始监控 {FEEDBACK_DIR}")
    print("[监控] 按 Ctrl+C 停止")
    processed = set()
    try:
        while True:
            for f in sorted(FEEDBACK_DIR.glob("feedback_*.json")):
                if f.name in processed:
                    continue
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if data.get("feedback") is not None:
                        processed.add(f.name)
                        continue
                    result = evaluate_answer(data.get("question", ""), data.get("transcript", ""), data.get("category", "general"))
                    data["feedback"] = result
                    data["processed_at"] = datetime.now().isoformat()
                    with open(f, "w", encoding="utf-8") as fh:
                        json.dump(data, fh, ensure_ascii=False, indent=2)
                    processed.add(f.name)
                    print(f"  [自动处理] {f.name}")
                except Exception as e:
                    print(f"  [错误] {f.name}: {e}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n[监控] 已停止")


def main():
    parser = argparse.ArgumentParser(description="反馈处理工具")
    parser.add_argument("--watch", action="store_true", help="持续监控模式")
    args = parser.parse_args()

    if args.watch:
        watch_mode()
    else:
        count = process_pending()
        print(f"\n处理完成: {count} 条反馈")


if __name__ == "__main__":
    main()
