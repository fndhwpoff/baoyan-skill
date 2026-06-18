#!/usr/bin/env python3
"""保研skill — 本地Web服务器 v2.1

提供:
  - 静态文件服务 (web/ 目录)
  - GET  /api/questions            — 题库数据 (?lang=cn|en, ?sample=10)
  - GET  /api/notices              — 通知数据
  - POST /api/notices/refresh      — 触发重新抓取
  - POST /api/notices/merge-websearch — 合并WebSearch结果
  - GET  /api/experiences          — 面试经验数据
  - POST /api/feedback             — AI反馈提交
  - GET  /api/feedback/check       — 检查反馈结果 ?session=xxx
  - GET  /api/results              — 成果列表
  - GET  /api/results/content      — 读取成果文件 ?path=xxx
  - GET/POST /api/interview        — 模拟面试
  - GET  /api/health               — 健康检查
"""

import argparse, json, os, random, subprocess, sys, uuid
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DEFAULT_WEB_DIR = SKILL_DIR / "web"
DEFAULT_QUESTIONS_DIR = SKILL_DIR / "data" / "questions"
DEFAULT_NOTICES_DIR = SKILL_DIR / "data" / "notices"
DEFAULT_EXPERIENCES_DIR = SKILL_DIR / "data" / "experiences"
OUTPUT_DIR = SKILL_DIR / "output"


class PracticeServerHandler(SimpleHTTPRequestHandler):
    web_dir = str(DEFAULT_WEB_DIR)
    questions_file = str(DEFAULT_QUESTIONS_DIR / "index.json")
    notices_file = str(DEFAULT_NOTICES_DIR / "index.json")
    experiences_file = str(DEFAULT_EXPERIENCES_DIR / "index.json")
    scraper_script = str(SKILL_DIR / "tools" / "notice_scraper.py")
    schools_config = str(SKILL_DIR / "config" / "schools.yaml")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self):
        p = urlparse(self.path)
        routes = {
            "/api/questions": lambda: self.serve_questions(p),
            "/api/notices": self.serve_notices,
            "/api/experiences": lambda: self.serve_experiences(p),
            "/api/interview": lambda: self.serve_interview_state(p),
            "/api/results": self.serve_results,
            "/api/results/content": lambda: self.serve_results_content(p),
            "/api/feedback/check": lambda: self.serve_feedback_result(p),
            "/api/health": lambda: self.serve_json({"status": "ok", "message": "保研skill v2.1 Server running"}),
        }
        if p.path in routes:
            routes[p.path]()
            return
        super().do_GET()

    def do_POST(self):
        p = urlparse(self.path)
        routes = {
            "/api/notices/refresh": self.refresh_notices,
            "/api/notices/merge-websearch": self.merge_websearch,
            "/api/feedback": self.handle_feedback,
            "/api/interview": self.handle_interview,
        }
        if p.path in routes:
            routes[p.path]()
            return
        self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── Results API (成果中心) ──

    def serve_results(self):
        """列出 output/ 目录下所有生成文件"""
        try:
            files = []
            categories = {
                "resume": "resume", "questions": "questions",
                "ps": "ps", "email": "email",
                "recommend": "recommend", "exam": "exam", "compare": "compare",
            }
            for cat_key, cat_dir in categories.items():
                cat_path = OUTPUT_DIR / cat_dir
                if not cat_path.exists():
                    continue
                for f in sorted(cat_path.iterdir(), reverse=True):
                    if f.suffix in (".md", ".txt") and f.name != ".gitkeep":
                        stat = f.stat()
                        files.append({
                            "name": f.name,
                            "path": str(f.relative_to(SKILL_DIR)),
                            "category": cat_key,
                            "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "size": f"{stat.st_size // 1024} KB",
                        })
            self.serve_json({"files": files, "total": len(files)})
        except Exception as e:
            self.serve_json({"error": str(e), "files": []}, status=500)

    def serve_results_content(self, parsed):
        """读取指定文件内容"""
        try:
            qs = parse_qs(parsed.query)
            path = qs.get("path", [None])[0]
            if not path:
                self.serve_json({"error": "缺少 path 参数"}, status=400)
                return
            full_path = SKILL_DIR / path
            # 安全检查：只允许 output/ 和 data/ 目录
            allowed = [str(OUTPUT_DIR), str(SKILL_DIR / "data")]
            if not any(str(full_path).startswith(a) for a in allowed):
                self.serve_json({"error": "不允许访问该路径"}, status=403)
                return
            if not full_path.exists():
                self.serve_json({"error": "文件不存在"}, status=404)
                return
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.serve_json({"content": content, "name": full_path.name})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    # ── Questions API ──

    def serve_questions(self, parsed=None):
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"sessions": {}, "message": "题库为空"}

            # 语言过滤
            lang = "all"
            if parsed:
                qs = parse_qs(parsed.query)
                lang = qs.get("lang", ["all"])[0]
                if lang in ("cn", "en"):
                    data = self._filter_questions_by_lang(data, lang)

            # 随机抽样（?sample=N），默认不抽样返回全部
            if parsed:
                qs = parse_qs(parsed.query)
                sample_n = int(qs.get("sample", [0])[0])
                if sample_n > 0:
                    data = self._sample_questions(data, sample_n)

            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def _filter_questions_by_lang(self, data, lang):
        filtered_sessions = {}
        for session_name, session_data in data.get("sessions", {}).items():
            questions = session_data if isinstance(session_data, list) else session_data.get("questions", [])
            filtered = [q for q in questions if q.get("language", "") == lang or (lang == "en" and not q.get("language"))]
            if filtered:
                filtered_sessions[session_name] = filtered
        return {"sessions": filtered_sessions, "message": f"filtered: {lang}"}

    def _sample_questions(self, data, n):
        """随机抽取 n 道题"""
        for session_name, questions in data.get("sessions", {}).items():
            if len(questions) > n:
                data["sessions"][session_name] = random.sample(questions, n)
                data["message"] = f"random sample: {n}/{len(questions)}"
        return data

    # ── Notices API ──

    def serve_notices(self):
        try:
            notices_data = {"updated_at": None, "schools": {}}
            if os.path.exists(self.notices_file):
                with open(self.notices_file, "r", encoding="utf-8") as f:
                    notices_data = json.load(f)
            import yaml
            schools_config = {}
            if os.path.exists(self.schools_config):
                with open(self.schools_config, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                    for s in raw.get("schools", []):
                        schools_config[s["short"]] = {"name": s["name"], "level": s.get("level", ""), "college": s.get("college", "")}
            for short, school_data in notices_data.get("schools", {}).items():
                school_data["_config"] = schools_config.get(short, {})
            self.serve_json(notices_data)
        except Exception as e:
            self.serve_json({"error": str(e), "schools": {}}, status=500)

    def serve_experiences(self, parsed=None):
        try:
            if os.path.exists(self.experiences_file):
                with open(self.experiences_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"experiences": {}}
            if parsed:
                qs = parse_qs(parsed.query)
                school = qs.get("school", [None])[0]
                if school and school in data.get("experiences", {}):
                    data = {"experiences": {school: data["experiences"][school]}}
            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e), "experiences": {}}, status=500)

    def serve_interview_state(self, parsed=None):
        try:
            qs = parse_qs(parsed.query) if parsed else {}
            session_id = qs.get("session", [None])[0]
            if session_id == "latest":
                # 找最新的会话文件
                import glob
                pattern = str(SKILL_DIR / "data" / "interview_session_*.json")
                files = glob.glob(pattern)
                if files:
                    latest = max(files, key=os.path.getmtime)
                    with open(latest, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.serve_json(data)
                    return
                self.serve_json({"status": "no_session", "conversation": []})
                return
            session_file = SKILL_DIR / "data" / f"interview_session_{session_id}.json"
            if session_id and session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"status": "no_session", "conversation": []}
            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e), "conversation": []}, status=500)

    # ── Feedback API ──

    def handle_feedback(self):
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
                "created_at": datetime.now().isoformat(),
                "feedback": None,
            }

            feedback_dir = SKILL_DIR / "data" / "feedback"
            feedback_dir.mkdir(parents=True, exist_ok=True)
            feedback_file = feedback_dir / f"feedback_{session_id}.json"
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)

            self.serve_json({
                "session_id": session_id,
                "status": "pending",
                "hint": "请在 Claude Code 中输入 /保研 feedback 获取 AI 点评",
            })
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def serve_feedback_result(self, parsed):
        """轮询反馈结果"""
        try:
            qs = parse_qs(parsed.query)
            session_id = qs.get("session", [None])[0]
            if not session_id:
                self.serve_json({"status": "no_session"}, status=400)
                return
            feedback_file = SKILL_DIR / "data" / "feedback" / f"feedback_{session_id}.json"
            if feedback_file.exists():
                with open(feedback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("feedback"):
                    self.serve_json({"status": "done", "feedback": data["feedback"]})
                else:
                    self.serve_json({"status": "pending"})
            else:
                self.serve_json({"status": "not_found"})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    # ── Interview API ──

    def handle_interview(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            req = json.loads(body)
            session_id = req.get("session_id", str(uuid.uuid4())[:8])
            session_file = SKILL_DIR / "data" / f"interview_session_{session_id}.json"
            session_data = {
                "session_id": session_id,
                "conversation": req.get("conversation", []),
                "current_question_index": req.get("current_question_index", 0),
                "round_in_question": req.get("round_in_question", 0),
                "questions": req.get("questions", []),
                "updated_at": datetime.now().isoformat(),
                "status": req.get("status", "ongoing"),
                "evaluation": req.get("evaluation", None),
            }
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            self.serve_json({"session_id": session_id, "status": "ok"})
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    # ── POST: Notice operations ──

    def refresh_notices(self):
        try:
            import yaml
            shorts = "all"
            if os.path.exists(self.schools_config):
                with open(self.schools_config, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                    shorts = ",".join(s["short"] for s in raw.get("schools", []))
            result = subprocess.run(
                ["python", self.scraper_script, "--school", shorts, "--output", self.notices_file, "--refresh"],
                capture_output=True, text=True, timeout=120, cwd=str(SKILL_DIR),
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"[scraper error] {result.stderr}")
            if os.path.exists(self.notices_file):
                with open(self.notices_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"updated_at": None, "schools": {}}
            self.serve_json(data)
        except subprocess.TimeoutExpired:
            self.serve_json({"error": "抓取超时", "schools": {}}, status=504)
        except Exception as e:
            self.serve_json({"error": str(e), "schools": {}}, status=500)

    def merge_websearch(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            req = json.loads(body)
            school = req.get("school", "")
            notices = req.get("notices", [])
            if not school:
                self.serve_json({"error": "缺少 school 参数"}, status=400)
                return
            sys.path.insert(0, str(SKILL_DIR / "tools"))
            from notice_scraper import merge_websearch_results
            merge_websearch_results(school, notices)
            self.serve_json({"ok": True, "school": school, "count": len(notices)})
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
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--web-dir", default=str(DEFAULT_WEB_DIR))
    parser.add_argument("--data-dir", default=str(DEFAULT_QUESTIONS_DIR))
    args = parser.parse_args()
    web_dir = Path(args.web_dir)
    if not web_dir.exists():
        print(f"[错误] Web 目录不存在: {web_dir}")
        sys.exit(1)
    questions_dir = Path(args.data_dir)
    PracticeServerHandler.web_dir = str(web_dir)
    PracticeServerHandler.questions_file = str(questions_dir / "index.json")
    PracticeServerHandler.notices_file = str(questions_dir.parent / "notices" / "index.json")
    server = HTTPServer(("127.0.0.1", args.port), PracticeServerHandler)
    print("=" * 55)
    print("  保研skill v2.1 — Web 服务器")
    print("=" * 55)
    print(f"  [面试练习]    http://localhost:{args.port}")
    print(f"  [通知看板]    http://localhost:{args.port}/notices.html")
    print(f"  [成果中心]    http://localhost:{args.port}/results.html")
    print(f"  [模拟面试]    http://localhost:{args.port}/interviewer.html")
    print(f"  [健康检查]    http://localhost:{args.port}/api/health")
    print(f"  按 Ctrl+C 停止")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()
