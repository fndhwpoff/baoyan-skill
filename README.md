# 保研 Skill v2.0

> 机械工程保研全流程助手：从材料准备、信息搜集到面试练习，一站式搞定  
> Claude Code Skill · 开源 · 零数据上传

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)]()

---

## 功能一览

### 📝 材料准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 🇬🇧 简历翻译 | 中文简历 → 专业英文简历（含机械工程术语表） | `/保研 resume` |
| 📄 个人陈述 | 定制化 1500-2000 字中文个人陈述（5段式） | `/保研 ps` |
| ✉️ 联系导师邮件 | 300-500字学术联系邮件（含具体论文引用） | `/保研 email` |
| 📨 推荐信草稿 | 教授视角推荐信（学术型/竞赛型） | `/保研 recommend` |

### 🎤 面试准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 📋 面试题生成 | 基于简历生成中英文面试问题（技术/行为/通用三维度） | `/保研 resume` |
| 🎥 口语练习 | 浏览器端中英文面试练习，摄像头录制+回放 | `/保研 practice` |
| 🤖 AI 面试反馈 | 语音转写 → AI 评估（内容/流利度/逻辑三维度打分） | `/保研 feedback` |
| 🎓 AI 模拟面试官 | 对话式追问面试，3-4轮追问/题 → 综合评估 | `/保研 mock` |
| 📚 面经搜索 | 搜索知乎/保研论坛面经，结构化存储 | `/保研 experience` |

### 📡 信息搜集 & 决策
| 功能 | 说明 | 命令 |
|------|------|------|
| 📡 通知聚合 | 18校夏令营/预推免通知自动抓取 + WebSearch 兜底 | `/保研 notice` |
| 🖥️ 通知 Dashboard | Web看板：搜索/筛选/排序/截止倒计时/来源标记 | `notices.html` |
| 📖 笔试备考 | 机械核心课分科备考指南（6门课+各校风格） | `/保研 exam` |
| ⚖️ Offer 对比 | 8维对比分析 + 评分 + 建议 | `/保研 compare` |

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

### 1️⃣ 材料准备流程

```
/保研 resume      # 翻译简历 + 生成面试题
/保研 ps           # 生成个人陈述
/保研 email        # 生成联系导师邮件
/保研 recommend    # 生成推荐信草稿
```

### 2️⃣ 查通知 + 备考

```
/保研 notice       # 抓取夏令营/预推免通知
/保研 exam         # 生成笔试备考指南
/保研 compare      # 对比多个Offer
```

### 3️⃣ 面试练习

```
/保研 practice     # 浏览器中英文面试练习（摄像头录制）
/保研 feedback     # AI点评面试回答
/保研 mock         # AI模拟面试官（追问式）
/保研 experience   # 搜索各校面试经验
```

### 4️⃣ Web 页面

```bash
/保研 serve        # 启动本地 Web 服务
```

| 页面 | 地址 | 功能 |
|------|------|------|
| 🎥 面试练习 | `http://localhost:8765` | 中英文面试练习，摄像头录制，AI点评 |
| 📡 通知 Dashboard | `http://localhost:8765/notices.html` | 通知聚合看板，截止倒计时，筛选排序 |
| 🤖 模拟面试官 | `http://localhost:8765/interviewer.html` | AI追问式面试对话展示 |

---

## 项目结构

```
保研skill/
├── SKILL.md                         # 入口文件 (v2.0)
├── prompts/                         # 提示词模板 (10个)
│   ├── resume_translate_en.md       #  简历翻译
│   ├── interview_questions_cn.md    #  中文面试题生成
│   ├── interview_questions_en.md    #  英文面试题生成
│   ├── notice_analysis.md           #  通知语义解析
│   ├── personal_statement_cn.md     #  个人陈述 (NEW)
│   ├── advisor_email_cn.md          #  联系导师邮件 (NEW)
│   ├── recommendation_letter_cn.md  #  推荐信 (NEW)
│   ├── exam_prep.md                 #  笔试备考 (NEW)
│   ├── school_compare.md            #  Offer对比 (NEW)
│   └── experience_summary.md        #  面经提取 (NEW)
├── tools/                           # Python 工具 (4个)
│   ├── notice_scraper.py            #  通知爬虫 (v2升级)
│   ├── question_store.py            #  题库管理
│   ├── experience_store.py          #  面经库管理 (NEW)
│   └── web_server.py                #  Web服务器 (v2升级)
├── config/schools.yaml              # 18校配置
├── data/                            # 持久化数据
│   ├── notices/                     #  通知缓存
│   ├── questions/                   #  题库
│   ├── experiences/                 #  面经库 (NEW)
│   ├── feedback/                    #  AI反馈 (NEW)
│   └── exam_topics.json             #  笔试知识点 (NEW)
├── output/                          # 用户生成文件
│   ├── resume/  ├── questions/
│   ├── ps/      ├── email/         # (NEW)
│   ├── recommend/  ├── exam/       # (NEW)
│   └── compare/                    # (NEW)
└── web/                             # 前端页面 (3个)
    ├── index.html                   #  面试练习 (支持中英文)
    ├── notices.html                 #  通知Dashboard (v2升级)
    ├── interviewer.html             #  模拟面试官 (NEW)
    ├── css/style.css
    └── js/ (app.js, camera.js, question_loader.js)
```

---

## 覆盖学校

| 层次 | 学校 |
|------|------|
| C9 | 清华、北大、上交、浙大、西交、哈工大、哈工深、中科大 |
| 机械强校985 | 同济、华科、北航、北理、大工、天大、西工大、东大、华工、重大 |

共 18 所。在 `config/schools.yaml` 中可增删改查。

> ⚠️ 部分学校的通知页 URL 可能失效，遇到抓取失败时会自动使用 WebSearch 兜底。

---

## 隐私

- ✅ 所有数据本地存储，不上传任何服务器
- ✅ 简历、面试题、练习录制均在你的电脑上
- ✅ 网页录制的视频仅存浏览器内存，关闭即消失
- ✅ 语音转写使用浏览器内置 Web Speech API（Chrome/Edge）
- ✅ 通知爬虫仅读取公开网页

---

## v2.0 更新内容

相比 v1.0，v2.0 新增：

- 🆕 **个人陈述生成** — 5段式定制化PS
- 🆕 **联系导师邮件** — 带论文引用的学术邮件
- 🆕 **推荐信草稿** — 学术型/竞赛型双模式
- 🆕 **笔试备考指南** — 6门核心课 + 各校风格
- 🆕 **Offer 对比工具** — 8维评分 + 雷达图
- 🆕 **AI 面试反馈** — 语音转写 + 三维度评估
- 🆕 **AI 模拟面试官** — 追问式对话面试
- 🆕 **面经搜索** — 结构化经验库
- 🆕 **中文面试模式** — 面试练习支持中英切换
- 🆕 **截止日期倒计时** — Dashboard 颜色预警
- 🆕 **WebSearch 兜底** — 爬虫失败自动搜索
- 🆕 **移动端优化** — 480px 响应式断点

---

## License

MIT © [fndhwpoff](https://github.com/fndhwpoff)
