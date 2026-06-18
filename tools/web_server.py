#!/usr/bin/env python3
"""保研skill — 本地Web服务器

提供:
  - 静态文件服务 (web/ 目录)
  - GET  /api/questions           — 题库数据 (?lang=cn|en)
  - GET  /api/notices             — 通知数据
  - POST /api/notices/refresh     — 触发重新抓取
  - POST /api/notices/merge-websearch — 合并WebSearch结果
  - POST /api/feedback            — AI反馈中转
  - GET  /api/experiences         — 面试经验数据
  - POST /api/interview           — 模拟面试中转
  - GET  /api/interview           — 获取面试会话状态
  - GET  /api/health              — 健康检查

用法:
  python web_server.py --port 8765
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 默认路径
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DEFAULT_WEB_DIR = SKILL_DIR / "web"
DEFAULT_QUESTIONS_DIR = SKILL_DIR / "data" / "questions"
DEFAULT_NOTICES_DIR = SKILL_DIR / "data" / "notices"
DEFAULT_EXPERIENCES_DIR = SKILL_DIR / "data" / "experiences"


class PracticeServerHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    web_dir = str(DEFAULT_WEB_DIR)
    questions_file = str(DEFAULT_QUESTIONS_DIR / "index.json")
    notices_file = str(DEFAULT_NOTICES_DIR / "index.json")
    experiences_file = str(DEFAULT_EXPERIENCES_DIR / "index.json")
    scraper_script = str(SKILL_DIR / "tools" / "notice_scraper.py")
    schools_config = str(SKILL_DIR / "config" / "schools.yaml")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/questions":
            self.serve_questions(parsed)
            return
        if parsed.path == "/api/notices":
            self.serve_notices()
            return
        if parsed.path == "/api/experiences":
            self.serve_experiences(parsed)
            return
        if parsed.path == "/api/interview":
            self.serve_interview_state(parsed)
            return
        if parsed.path == "/api/health":
            self.serve_json({"status": "ok", "message": "保研skill Server running"})
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/notices/refresh":
            self.refresh_notices()
            return
        if parsed.path == "/api/notices/merge-websearch":
            self.merge_websearch()
            return
        if parsed.path == "/api/feedback":
            self.handle_feedback()
            return
        if parsed.path == "/api/interview":
            self.handle_interview()
            return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── READ endpoints ──

    def serve_questions(self, parsed=None):
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"sessions": {}, "message": "题库为空"}

            # 支持 ?lang=cn 过滤
            if parsed:
                qs = parse_qs(parsed.query)
                lang = qs.get("lang", ["all"])[0]
                if lang in ("cn", "en"):
                    data = self._filter_questions_by_lang(data, lang)

            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def _filter_questions_by_lang(self, data, lang):
        """按语言过滤问题"""
        filtered_sessions = {}
        for session_name, questions in data.get("sessions", {}).items():
            filtered = []
            for q in questions:
                q_lang = q.get("language", "")
                if q_lang == lang or (lang == "en" and q_lang == ""):
                    filtered.append(q)
            if filtered:
                filtered_sessions[session_name] = filtered
        return {"sessions": filtered_sessions, "message": f"已过滤：{lang}"}

    def serve_notices(self):
        """返回缓存的通知 JSON + 学校配置"""
        try:
            notices_data = {"updated_at": None, "schools": {}}
            if os.path.exists(self.notices_file):
                with open(self.notices_file, "r", encoding="utf-8") as f:
                    notices_data = json.load(f)

            # 加载学校配置（补充学校名、层次信息）
            import yaml
            schools_config = {}
            if os.path.exists(self.schools_config):
                with open(self.schools_config, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                    for s in raw.get("schools", []):
                        schools_config[s["short"]] = {
                            "name": s["name"],
                            "level": s.get("level", ""),
                            "college": s.get("college", ""),
                        }

            # 合并学校信息到通知中
            for short, school_data in notices_data.get("schools", {}).items():
                school_data["_config"] = schools_config.get(short, {})

            self.serve_json(notices_data)
        except Exception as e:
            self.serve_json({"error": str(e), "schools": {}}, status=500)

    def serve_experiences(self, parsed=None):
        """返回面试经验数据，支持 ?school=上交 过滤"""
        try:
            if os.path.exists(self.experiences_file):
                with open(self.experiences_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"experiences": {}}

            # 支持按学校过滤
            if parsed:
                qs = parse_qs(parsed.query)
                school = qs.get("school", [None])[0]
                if school and school in data.get("experiences", {}):
                    data = {"experiences": {school: data["experiences"][school]}}

            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e), "experiences": {}}, status=500)

    def serve_interview_state(self, parsed=None):
        """获取模拟面试会话状态"""
        try:
            qs = parse_qs(parsed.query) if parsed else {}
            session_id = qs.get("session", [None])[0]
            session_file = SKILL_DIR / "data" / f"interview_session_{session_id}.json"

            if session_id and session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"status": "no_session", "conversation": []}

            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e), "conversation": []}, status=500)

    # ── POST endpoints ──

    def refresh_notices(self):
        """触发重新抓取通知"""
        try:
            # 先读取学校配置获取所有简称
            import yaml
            shorts = "all"
            if os.path.exists(self.schools_config):
                with open(self.schools_config, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                    shorts = ",".join(s["short"] for s in raw.get("schools", []))

            # 运行抓取脚本
            result = subprocess.run(
                ["python", self.scraper_script, "--school", shorts, "--output", self.notices_file, "--refresh"],
                capture_output=True, text=True, timeout=120, cwd=str(SKILL_DIR),
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"[scraper error] {result.stderr}")

            # 返回更新后的数据
            if os.path.exists(self.notices_file):
                with open(self.notices_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"updated_at": None, "schools": {}}

            self.serve_json(data)
        except subprocess.TimeoutExpired:
            self.serve_json({"error": "抓取超时（>120秒）", "schools": {}}, status=504)
        except Exception as e:
            self.serve_json({"error": str(e), "schools": {}}, status=500)

    def merge_websearch(self):
        """接收 WebSearch 结果并合并到通知缓存"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            req = json.loads(body)

            school = req.get("school", "")
            notices = req.get("notices", [])

            if not school:
                self.serve_json({"error": "缺少 school 参数"}, status=400)
                return

            # 调用 scraper 的 merge 函数
            sys.path.insert(0, str(SKILL_DIR / "tools"))
            from notice_scraper import merge_websearch_results
            merge_websearch_results(school, notices)

            self.serve_json({"ok": True, "school": school, "count": len(notices)})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def handle_feedback(self):
        """接收面试回答文本，写入临时文件供 Claude 分析"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            req = json.loads(body)

            question = req.get("question", "")
            transcript = req.get("transcript", "")
            category = req.get("category", "general")

            session_id = str(uuid.uuid4())[:8]
            feedback_data = {
                "session_id": session_id,
                "question": question,
                "transcript": transcript,
                "category": category,
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "feedback": None,  # Claude 填写后写回
            }

            # 写入临时文件
            feedback_dir = SKILL_DIR / "data" / "feedback"
            feedback_dir.mkdir(parents=True, exist_ok=True)
            feedback_file = feedback_dir / f"feedback_{session_id}.json"
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)

            self.serve_json({"session_id": session_id, "status": "pending",
                             "hint": "请在 Claude Code 中输入 /保研 feedback 获取 AI 点评"})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def handle_interview(self):
        """接收/更新模拟面试会话"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            req = json.loads(body)

            session_id = req.get("session_id", str(uuid.uuid4())[:8])
            session_file = SKILL_DIR / "data" / f"interview_session_{session_id}.json"

            # 写入会话数据
            session_data = {
                "session_id": session_id,
                "conversation": req.get("conversation", []),
                "current_question_index": req.get("current_question_index", 0),
                "round_in_question": req.get("round_in_question", 0),
                "questions": req.get("questions", []),
                "updated_at": __import__("datetime").datetime.now().isoformat(),
                "status": req.get("status", "ongoing"),
                "evaluation": req.get("evaluation", None),
            }
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            self.serve_json({"session_id": session_id, "status": "ok"})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    # ── Helpers ──

    def serve_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"  {args[0]} {args[1]}")


def main():
    parser = argparse.ArgumentParser(description="保研skill — Web服务器")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认: 8765)")
    parser.add_argument("--web-dir", default=str(DEFAULT_WEB_DIR), help="静态文件目录")
    parser.add_argument("--data-dir", default=str(DEFAULT_QUESTIONS_DIR), help="题库目录")

    args = parser.parse_args()

    web_dir = Path(args.web_dir)
    if not web_dir.exists():
        print(f"[错误] Web 目录不存在: {web_dir}")
        sys.exit(1)

    questions_dir = Path(args.data_dir)
    notices_dir = questions_dir.parent / "notices"

    PracticeServerHandler.web_dir = str(web_dir)
    PracticeServerHandler.questions_file = str(questions_dir / "index.json")
    PracticeServerHandler.notices_file = str(notices_dir / "index.json")

    server = HTTPServer(("127.0.0.1", args.port), PracticeServerHandler)

    print("=" * 55)
    print("  保研skill v2.0 — Web 服务器")
    print("=" * 55)
    print(f"  [面试练习]  http://localhost:{args.port}")
    print(f"  [通知看板]  http://localhost:{args.port}/notices.html")
    print(f"  [模拟面试]  http://localhost:{args.port}/interviewer.html")
    print(f"  [健康检查]  http://localhost:{args.port}/api/health")
    print(f"  按 Ctrl+C 停止")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()
