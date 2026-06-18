#!/usr/bin/env python3
"""保研skill — 英文面试练习本地服务器

使用 Python 内置 http.server 提供：
  - 静态文件服务（web/ 目录下的 HTML/CSS/JS）
  - API 接口：GET /api/questions 返回题库数据

用法:
  python web_server.py --port 8765
  python web_server.py --port 8765 --web-dir web --data-dir data/questions
"""

import argparse
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# 默认路径
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
DEFAULT_WEB_DIR = SKILL_DIR / "web"
DEFAULT_DATA_DIR = SKILL_DIR / "data" / "questions"
QUESTIONS_FILE = DEFAULT_DATA_DIR / "index.json"


class PracticeServerHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    web_dir = str(DEFAULT_WEB_DIR)
    questions_file = str(QUESTIONS_FILE)

    def __init__(self, *args, **kwargs):
        # 设置静态文件根目录
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        # API 路由：返回面试题数据
        if parsed.path == "/api/questions":
            self.serve_questions()
            return

        # API 路由：健康检查
        if parsed.path == "/api/health":
            self.serve_json({"status": "ok", "message": "保研skill Practice Server is running"})
            return

        # 默认：静态文件服务
        super().do_GET()

    def serve_questions(self):
        """返回题库 JSON"""
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {
                    "sessions": {},
                    "message": "题库为空。请先生成英文面试题：在 Claude Code 中输入 /保研 resume",
                }
            self.serve_json(data)
        except Exception as e:
            self.serve_json({"error": str(e)}, status=500)

    def serve_json(self, data, status=200):
        """发送 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """格式化日志"""
        symbol = " "
        print(f"  {symbol} {args[0]} {args[1]}")


def main():
    parser = argparse.ArgumentParser(description="保研skill — 英文面试练习服务器")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认: 8765)")
    parser.add_argument("--web-dir", default=str(DEFAULT_WEB_DIR),
                        help=f"静态文件目录 (默认: {DEFAULT_WEB_DIR})")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR),
                        help=f"题库数据目录 (默认: {DEFAULT_DATA_DIR})")

    args = parser.parse_args()

    # 检查目录
    web_dir = Path(args.web_dir)
    if not web_dir.exists():
        print(f"[错误] Web 目录不存在: {web_dir}")
        sys.exit(1)
    if not (web_dir / "index.html").exists():
        print(f"[错误] index.html 不存在于: {web_dir}")
        sys.exit(1)

    data_dir = Path(args.data_dir)
    questions_file = data_dir / "index.json"

    # 配置处理器
    PracticeServerHandler.web_dir = str(web_dir)
    PracticeServerHandler.questions_file = str(questions_file)

    # 启动服务器
    server = HTTPServer(("127.0.0.1", args.port), PracticeServerHandler)

    print("=" * 50)
    print("  保研skill — 英文面试练习服务器")
    print("=" * 50)
    print(f"\n  Web 目录:  {web_dir}")
    print(f"  题库文件:  {questions_file}")
    if questions_file.exists():
        with open(questions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        sessions = data.get("sessions", {})
        total_q = sum(s.get("question_count", len(s.get("questions", []))) for s in sessions.values())
        print(f"  题库状态:  {len(sessions)} 个会话, {total_q} 道题目")
    else:
        print(f"  [!] 题库为空 — 请先生成面试题")
    print(f"\n  请在浏览器打开:\n")
    print(f"     >>> http://localhost:{args.port}")
    print(f"\n  按 Ctrl+C 停止服务器")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()
