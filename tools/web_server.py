#!/usr/bin/env python3
"""保研skill — 本地Web服务器

提供:
  - 静态文件服务 (web/ 目录)
  - GET  /api/questions      — 题库数据
  - GET  /api/notices        — 通知数据
  - POST /api/notices/refresh — 触发重新抓取
  - GET  /api/health         — 健康检查

用法:
  python web_server.py --port 8765
"""

import argparse
import json
import os
import subprocess
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# 默认路径
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DEFAULT_WEB_DIR = SKILL_DIR / "web"
DEFAULT_QUESTIONS_DIR = SKILL_DIR / "data" / "questions"
DEFAULT_NOTICES_DIR = SKILL_DIR / "data" / "notices"


class PracticeServerHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    web_dir = str(DEFAULT_WEB_DIR)
    questions_file = str(DEFAULT_QUESTIONS_DIR / "index.json")
    notices_file = str(DEFAULT_NOTICES_DIR / "index.json")
    scraper_script = str(SKILL_DIR / "tools" / "notice_scraper.py")
    schools_config = str(SKILL_DIR / "config" / "schools.yaml")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/questions":
            self.serve_questions()
            return
        if parsed.path == "/api/notices":
            self.serve_notices()
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

        self.send_response(404)
        self.end_headers()

    def serve_questions(self):
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"sessions": {}, "message": "题库为空"}
            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

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
    print("  保研skill — Web 服务器")
    print("=" * 55)
    print(f"  [面试练习]  http://localhost:{args.port}")
    print(f"  [通知看板]  http://localhost:{args.port}/notices.html")
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
