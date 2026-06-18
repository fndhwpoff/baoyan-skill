#!/usr/bin/env python3
"""保研skill — 本地Web服务器 v2.3

提供:
  - 静态文件服务 (web/ 目录) + PDF 文件服务 (output/ 目录)
  - GET  /api/questions            — 题库 (?lang=cn|en, ?sample=N)
  - GET  /api/notices              — 通知数据
  - POST /api/notices/refresh      — 触发抓取
  - POST /api/notices/merge-websearch — 合并WebSearch
  - GET  /api/experiences          — 面经
  - POST /api/feedback             — 提交反馈
  - GET  /api/feedback/check       — 检查结果
  - POST /api/feedback/process     — 批量处理待反馈
  - GET  /api/results              — 成果列表 (?include_pdf=1)
  - GET  /api/results/content      — 读取文件
  - POST /api/results/generate-pdf — 批量生成PDF
  - GET/POST /api/interview        — 模拟面试
  - GET  /api/health               — 健康检查
"""

import argparse, json, os, random, subprocess, sys, threading, uuid
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", Path(__file__).parent.parent))
WEB_DIR = SKILL_DIR / "web"
QUESTIONS_FILE = SKILL_DIR / "data" / "questions" / "index.json"
NOTICES_FILE = SKILL_DIR / "data" / "notices" / "index.json"
EXPERIENCES_FILE = SKILL_DIR / "data" / "experiences" / "index.json"
OUTPUT_DIR = SKILL_DIR / "output"
SCRAPER_SCRIPT = SKILL_DIR / "tools" / "notice_scraper.py"
SCHOOLS_CONFIG = SKILL_DIR / "config" / "schools.yaml"
FEEDBACK_WORKER = SKILL_DIR / "tools" / "feedback_worker.py"
PDF_GENERATOR = SKILL_DIR / "tools" / "pdf_generator.py"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB_DIR), **kw)

    def do_GET(self):
        p = urlparse(self.path)
        # Serve PDF and HTML files from output/
        if p.path.startswith("/output/") and (p.path.endswith(".pdf") or p.path.endswith(".html")):
            self.serve_file(p.path)
            return
        routes = {
            "/api/questions": lambda: self.serve_questions(p),
            "/api/notices": self.serve_notices,
            "/api/experiences": lambda: self.serve_experiences(p),
            "/api/interview": lambda: self.serve_interview_state(p),
            "/api/results": lambda: self.serve_results(p),
            "/api/results/content": lambda: self.serve_results_content(p),
            "/api/feedback/check": lambda: self.serve_feedback_result(p),
            "/api/health": lambda: self.json({"status": "ok", "message": "保研skill v2.3" }),
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
            "/api/feedback/process": self.process_feedback,
            "/api/interview": self.handle_interview,
            "/api/results/generate-pdf": self.generate_pdfs,
        }
        if p.path in routes:
            routes[p.path]()
            return
        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── File serving ──
    def serve_file(self, path):
        fp = SKILL_DIR / path.lstrip("/")
        if not fp.exists():
            self.send_error(404); return
        ct = "text/html" if fp.suffix == ".html" else "application/pdf"
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(fp.stat().st_size))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open(fp, "rb") as f:
            self.wfile.write(f.read())

    # ── Results ──
    def serve_results(self, parsed=None):
        try:
            include_pdf = False
            if parsed:
                qs = parse_qs(parsed.query)
                include_pdf = qs.get("include_pdf", ["0"])[0] == "1"
            # Load school shorts for filename matching
            school_shorts = []
            if SCHOOLS_CONFIG.exists():
                import yaml
                with open(SCHOOLS_CONFIG,"r",encoding="utf-8") as f:
                    school_shorts = [s["short"] for s in yaml.safe_load(f).get("schools",[])]
            school_names = {s:s for s in school_shorts}
            files = []
            cats = {"resume":"resume","questions":"questions","ps":"ps","email":"email","recommend":"recommend","exam":"exam","compare":"compare"}
            for ck, cd in cats.items():
                cp = OUTPUT_DIR / cd
                if not cp.exists(): continue
                for f in sorted(cp.iterdir(), reverse=True):
                    if f.suffix in (".md",".txt") and f.name != ".gitkeep":
                        s = f.stat()
                        rel = str(f.relative_to(SKILL_DIR)).replace("\\","/")
                        # Extract school from filename
                        school = None
                        for sn in school_shorts:
                            if f"_{sn}" in f.stem or f.stem.startswith(f"{sn}_"):
                                school = sn; break
                        entry = {"name":f.name,"path":rel,"category":ck,"school":school,"date":datetime.fromtimestamp(s.st_mtime).isoformat(),"size":f"{s.st_size//1024} KB"}
                        # Check for HTML and PDF
                        if f.with_suffix(".html").exists():
                            entry["html"] = str(f.with_suffix(".html").relative_to(SKILL_DIR)).replace("\\","/")
                        if f.with_suffix(".pdf").exists():
                            entry["pdf"] = str(f.with_suffix(".pdf").relative_to(SKILL_DIR)).replace("\\","/")
                        files.append(entry)
            # Build school summary
            schools = {}
            for f in files:
                if f["school"]:
                    sn = f["school"]
                    if sn not in schools: schools[sn] = {"count":0,"categories":set()}
                    schools[sn]["count"] += 1
                    schools[sn]["categories"].add(f["category"])
            for sn in schools:
                schools[sn]["categories"] = sorted(schools[sn]["categories"])
            self.json({"files":files,"total":len(files),"schools":schools})
        except Exception as e:
            self.json({"error":str(e),"files":[],"schools":{}},500)

    def serve_results_content(self, parsed):
        try:
            qs = parse_qs(parsed.query)
            path = qs.get("path",[None])[0]
            if not path: self.json({"error":"missing path"},400); return
            path = path.replace("\\","/")
            fp = SKILL_DIR / path
            if not str(fp).startswith(str(OUTPUT_DIR)) and not str(fp).startswith(str(SKILL_DIR/"data")):
                self.json({"error":"forbidden"},403); return
            if not fp.exists(): self.json({"error":"not found"},404); return
            with open(fp,"r",encoding="utf-8") as f:
                self.json({"content":f.read(),"name":fp.name})
        except Exception as e:
            self.json({"error":str(e)},500)

    def generate_pdfs(self):
        """触发批量 PDF 生成"""
        try:
            r = subprocess.run(["python",str(PDF_GENERATOR)],capture_output=True,text=True,timeout=120,cwd=str(SKILL_DIR))
            self.json({"ok":True,"output":r.stdout,"errors":r.stderr})
        except subprocess.TimeoutExpired:
            self.json({"error":"PDF generation timeout"},504)
        except Exception as e:
            self.json({"error":str(e)},500)

    # ── Questions ──
    def serve_questions(self, parsed=None):
        try:
            data = {"sessions":{}}
            if QUESTIONS_FILE.exists():
                with open(QUESTIONS_FILE,"r",encoding="utf-8") as f:
                    data = json.load(f)
            lang, sample = "all", 0
            if parsed:
                qs = parse_qs(parsed.query)
                lang = qs.get("lang",["all"])[0]
                sample = int(qs.get("sample",[0])[0])
            if lang in ("cn","en"):
                data = self._filter_lang(data,lang)
            if sample > 0:
                data = self._sample(data,sample)
            self.json(data)
        except Exception as e:
            self.json({"error":str(e)},500)

    def _filter_lang(self,data,lang):
        fs={}
        for sn,sd in data.get("sessions",{}).items():
            qs=sd if isinstance(sd,list) else sd.get("questions",[])
            f=[q for q in qs if q.get("language","")==lang or (lang=="en" and not q.get("language"))]
            if f:fs[sn]=f
        return {"sessions":fs}

    def _sample(self,data,n):
        for sn,qs in data.get("sessions",{}).items():
            if len(qs)>n: data["sessions"][sn]=random.sample(qs,n)
        return data

    # ── Notices ──
    def serve_notices(self):
        try:
            nd = {"updated_at":None,"schools":{}}
            if NOTICES_FILE.exists():
                with open(NOTICES_FILE,"r",encoding="utf-8") as f:
                    nd = json.load(f)
            if SCHOOLS_CONFIG.exists():
                import yaml
                with open(SCHOOLS_CONFIG,"r",encoding="utf-8") as f:
                    sc = {s["short"]:{"name":s["name"],"level":s.get("level",""),"college":s.get("college","")} for s in yaml.safe_load(f).get("schools",[])}
                for short,sd in nd.get("schools",{}).items():
                    sd["_config"]=sc.get(short,{})
            self.json(nd)
        except Exception as e:
            self.json({"error":str(e),"schools":{}},500)

    def serve_experiences(self, parsed=None):
        try:
            data = {"experiences":{}}
            if EXPERIENCES_FILE.exists():
                with open(EXPERIENCES_FILE,"r",encoding="utf-8") as f:
                    data = json.load(f)
            if parsed:
                qs = parse_qs(parsed.query)
                school = qs.get("school",[None])[0]
                if school and school in data.get("experiences",{}):
                    data = {"experiences":{school:data["experiences"][school]}}
            self.json(data)
        except Exception as e:
            self.json({"error":str(e),"experiences":{}},500)

    def serve_interview_state(self, parsed=None):
        try:
            qs = parse_qs(parsed.query) if parsed else {}
            sid = qs.get("session",[None])[0]
            if sid == "latest":
                import glob
                files = glob.glob(str(SKILL_DIR/"data"/"interview_session_*.json"))
                if files:
                    with open(max(files,key=os.path.getmtime),"r",encoding="utf-8") as f:
                        self.json(json.load(f)); return
                self.json({"status":"no_session","conversation":[]}); return
            fp = SKILL_DIR/"data"/f"interview_session_{sid}.json"
            if sid and fp.exists():
                with open(fp,"r",encoding="utf-8") as f:
                    self.json(json.load(f))
            else:
                self.json({"status":"no_session","conversation":[]})
        except Exception as e:
            self.json({"error":str(e),"conversation":[]},500)

    # ── Feedback ──
    def handle_feedback(self):
        try:
            body = self._read_body()
            sid = str(uuid.uuid4())[:8]
            fd = {"session_id":sid,"question":body.get("question",""),"transcript":body.get("transcript",""),"category":body.get("category","general"),"created_at":datetime.now().isoformat(),"feedback":None}
            FEEDBACK_DIR = SKILL_DIR/"data"/"feedback"
            FEEDBACK_DIR.mkdir(parents=True,exist_ok=True)
            with open(FEEDBACK_DIR/f"feedback_{sid}.json","w",encoding="utf-8") as f:
                json.dump(fd,f,ensure_ascii=False,indent=2)
            # Auto-process immediately
            try:
                subprocess.Popen(["python",str(FEEDBACK_WORKER)],cwd=str(SKILL_DIR))
            except: pass
            self.json({"session_id":sid,"status":"pending","hint":"AI处理中，等待几秒后刷新查看结果..."})
        except Exception as e:
            self.json({"error":str(e)},500)

    def serve_feedback_result(self, parsed):
        try:
            qs = parse_qs(parsed.query)
            sid = qs.get("session",[None])[0]
            if not sid: self.json({"status":"no_session"},400); return
            fp = SKILL_DIR/"data"/"feedback"/f"feedback_{sid}.json"
            if fp.exists():
                with open(fp,"r",encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("feedback"): self.json({"status":"done","feedback":d["feedback"]})
                else: self.json({"status":"pending"})
            else: self.json({"status":"not_found"})
        except Exception as e:
            self.json({"error":str(e)},500)

    def process_feedback(self):
        """批量处理所有待反馈"""
        try:
            r = subprocess.run(["python",str(FEEDBACK_WORKER)],capture_output=True,text=True,timeout=30,cwd=str(SKILL_DIR))
            self.json({"ok":True,"output":r.stdout})
        except Exception as e:
            self.json({"error":str(e)},500)

    # ── Interview ──
    def handle_interview(self):
        try:
            body = self._read_body()
            sid = body.get("session_id",str(uuid.uuid4())[:8])
            sd = {"session_id":sid,"conversation":body.get("conversation",[]),"current_question_index":body.get("current_question_index",0),"round_in_question":body.get("round_in_question",0),"questions":body.get("questions",[]),"updated_at":datetime.now().isoformat(),"status":body.get("status","ongoing"),"evaluation":body.get("evaluation")}
            with open(SKILL_DIR/"data"/f"interview_session_{sid}.json","w",encoding="utf-8") as f:
                json.dump(sd,f,ensure_ascii=False,indent=2)
            self.json({"session_id":sid,"status":"ok"})
        except Exception as e:
            self.json({"error":str(e)},500)

    # ── POST: Notice ops ──
    def refresh_notices(self):
        try:
            import yaml; shorts="all"
            if SCHOOLS_CONFIG.exists():
                with open(SCHOOLS_CONFIG,"r",encoding="utf-8") as f:
                    shorts=",".join(s["short"] for s in yaml.safe_load(f).get("schools",[]))
            r=subprocess.run(["python",str(SCRAPER_SCRIPT),"--school",shorts,"--output",str(NOTICES_FILE),"--refresh"],capture_output=True,text=True,timeout=120,cwd=str(SKILL_DIR))
            if NOTICES_FILE.exists():
                with open(NOTICES_FILE,"r",encoding="utf-8") as f:
                    self.json(json.load(f))
            else: self.json({"updated_at":None,"schools":{}})
        except subprocess.TimeoutExpired: self.json({"error":"timeout","schools":{}},504)
        except Exception as e: self.json({"error":str(e),"schools":{}},500)

    def merge_websearch(self):
        try:
            body = self._read_body()
            school, notices = body.get("school",""), body.get("notices",[])
            if not school: self.json({"error":"missing school"},400); return
            sys.path.insert(0,str(SKILL_DIR/"tools"))
            from notice_scraper import merge_websearch_results
            merge_websearch_results(school,notices)
            self.json({"ok":True,"school":school,"count":len(notices)})
        except Exception as e: self.json({"error":str(e)},500)

    # ── Helpers ──
    def _read_body(self):
        cl = int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(cl)) if cl else {}

    def json(self, data, status=200):
        body = json.dumps(data,ensure_ascii=False,indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self,fmt,*a): print(f"  {a[0]} {a[1]}")


def main():
    p=argparse.ArgumentParser(description="保研skill Web服务器 v2.3")
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--watch-feedback",action="store_true",help="自动启动反馈监控")
    args=p.parse_args()
    if not WEB_DIR.exists(): print(f"[错误] Web目录不存在: {WEB_DIR}"); sys.exit(1)
    # Start feedback watcher
    if args.watch_feedback:
        def run_worker():
            subprocess.Popen(["python",str(FEEDBACK_WORKER),"--watch"],cwd=str(SKILL_DIR))
        threading.Thread(target=run_worker,daemon=True).start()
    server=HTTPServer(("127.0.0.1",args.port),Handler)
    print("="*55)
    print("  保研skill v2.3 — Web服务器")
    print("="*55)
    print(f"  [Home]        http://localhost:{args.port}")
    print(f"  [Practice]    http://localhost:{args.port}/practice.html")
    print(f"  [Notices]     http://localhost:{args.port}/notices.html")
    print(f"  [Results]     http://localhost:{args.port}/results.html")
    print(f"  [+PDF Gen]    POST /api/results/generate-pdf")
    print(f"  [+Auto Feed]  POST /api/feedback (auto-process)")
    print(f"  Ctrl+C to stop")
    print("="*55)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nServer stopped."); server.shutdown()


if __name__=="__main__": main()
