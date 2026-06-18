# 保研 Skill

> 机械工程保研全流程助手：英文简历 + 面试题库 + 通知聚合 + 口语练习  
> Claude Code Skill · 开源 · 零数据上传

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 功能一览

| 功能 | 说明 | 命令 |
|------|------|------|
| 📝 简历翻译 | 中文简历 → 专业英文简历（含机械工程术语表） | `/保研 resume` |
| 🎤 面试题生成 | 基于简历生成中英文面试问题（技术/行为/通用三维度） | 同上 |
| 📡 通知聚合 | 18所机械强校夏令营/预推免通知自动抓取 | `/保研 notice` |
| 🖥️ 通知看板 | Web Dashboard：搜索/筛选/排序/一键刷新 | `http://localhost:8765/notices.html` |
| 🎥 口语练习 | 摄像头模拟英文面试（准备计时+作答录制+回放） | `/保研 practice` |

---

## 安装

```bash
# 方式一：从 GitHub 安装到全局（推荐）
git clone https://github.com/fndhwpoff/baoyan-skill.git ~/.claude/skills/保研skill

# 方式二：安装到当前项目
mkdir -p .claude/skills
git clone https://github.com/fndhwpoff/baoyan-skill.git .claude/skills/保研skill
```

### 依赖

```bash
pip install -r ~/.claude/skills/保研skill/requirements.txt
```

---

## 快速使用

在 Claude Code 中输入斜杠命令即可：

### 1️⃣ 翻译简历 + 生成面试题

```
/保研 resume
```

按提示提供简历（粘贴/上传PDF/指定路径），AI 生成三份文件：

| 输出 | 路径 | 内容 |
|------|------|------|
| 🇬🇧 英文简历 | `output/resume/` | 完整 CV，ATS 友好格式 |
| 🇨🇳 中文面试题 | `output/questions/` | 15-20题，附考察目的+回答提示+追问 |
| 🇬🇧 英文面试题 | `output/questions/` | 8-12题，附中文翻译+面试技巧 |

生成后可选择**保存到题库**，供口语练习使用。

### 2️⃣ 查夏令营/预推免通知

```
/保研 notice
```

自动抓取 18 所学校的机械学院通知页，提取标题、链接、截止日期等信息。

**Web 看板**：启动服务器后打开 `http://localhost:8765/notices.html`，提供：

- 🔄 **一键刷新** — 实时重新抓取全部学校
- 🏷️ **筛选** — 夏令营 / 预推免 / C9 / 985
- 🔍 **搜索** — 学校名或标题关键字
- ↩️ **排序** — 点击表头按学校/类型排序
- 📊 **统计卡片** — 覆盖学校数、总通知数

### 3️⃣ 英文口语练习

```
/保研 practice
```

浏览器打开 `http://localhost:8765`，摄像头模拟面试：

- ⏱️ 30秒准备 → 90秒作答 → 回放查看
- 📹 录制内容仅在浏览器内存，关闭即消失
- 📋 题目来自你保存的英文题库

---

## 网页一览

启动 `python tools/web_server.py --port 8765` 后：

| 页面 | 地址 | 说明 |
|------|------|------|
| 🎥 面试练习 | `http://localhost:8765` | 摄像头模拟英文面试 |
| 📡 通知看板 | `http://localhost:8765/notices.html` | 通知聚合 Dashboard |

---

## 项目结构

```
保研skill/
├── SKILL.md                         # 入口文件（触发词+工作流）
├── prompts/                         # 提示词模板
│   ├── resume_translate_en.md       #  简历翻译规则
│   ├── interview_questions_cn.md    #  中文面试题生成
│   ├── interview_questions_en.md    #  英文面试题生成
│   └── notice_analysis.md           #  通知语义解析
├── tools/                           # Python 工具
│   ├── notice_scraper.py            #  通知爬虫（18校）
│   ├── question_store.py            #  面试题库管理
│   └── web_server.py                #  本地Web服务器
├── config/
│   └── schools.yaml                 # 学校列表+通知页URL
├── data/                            # 运行时数据
│   ├── notices/                     #  通知缓存
│   └── questions/                   #  题库
├── output/                          # 用户生成文件
├── web/                             # Web前端
│   ├── index.html                   #  面试练习页
│   ├── notices.html                 #  通知Dashboard
│   ├── css/style.css
│   └── js/
│       ├── app.js                   #  面试状态机
│       ├── camera.js                #  摄像头录制
│       └── question_loader.js       #  题目加载
└── requirements.txt
```

---

## 覆盖学校

| 层次 | 学校 |
|------|------|
| C9 | 清华、北大、上交、浙大、西交、哈工大、哈工深、中科大 |
| 机械强校985 | 同济、华科、北航、北理、大工、天大、西工大、东大、华工、重大 |

共 18 所。在 `config/schools.yaml` 中可增删改查。

> ⚠️ 部分学校的通知页 URL 为推测值，若抓取失败请提交 PR 修正。

---

## 隐私

- ✅ 所有数据本地存储，不上传任何服务器
- ✅ 简历、面试题、练习录制均在你的电脑上
- ✅ 网页录制的视频仅存浏览器内存，关闭即消失
- ✅ 通知爬虫仅读取公开网页

---

## License

MIT © [fndhwpoff](https://github.com/fndhwpoff)
