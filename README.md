# 保研 Skill v2.1

> 机械工程保研全流程助手：从材料准备、信息搜集到面试练习，一站式搞定  
> Claude Code Skill · 开源 · 零数据上传

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)]()

---

## 功能一览

### 📝 材料准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 🇬🇧 简历翻译 | 中文简历 → 专业英文简历（含机械工程术语表） | `/保研 resume` |
| 📄 个人陈述 | 定制化 1500-2000 字中文个人陈述（5段式） | `/保研 ps` |
| ✉️ 导师搜索与邮件 | 多导师搜索推荐（含风评来源标注）→ 学生选择 → 生成学术邮件 | `/保研 email` |
| 📨 推荐信草稿 | 教授视角推荐信（学术型/竞赛型） | `/保研 recommend` |

### 🎤 面试准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 📋 面试题生成 | 25-30题/语言 + **参考答案**（基于简历经历），随机抽10道练习 | `/保研 resume` |
| 🎥 口语练习 | 浏览器端中英文面试练习，摄像头录制+回放+**实时AI点评** | `/保研 practice` |
| 🤖 AI 面试反馈 | 语音转写 → 网页轮询 → 直接显示评分（内容/流利度/逻辑） | 练习页内置 |
| 🎓 AI 模拟面试官 | 对话式追问面试，3-4轮追问/题 → 综合评估 | `/保研 mock` |
| 📚 面经搜索 | 搜索知乎/保研论坛面经，结构化存储 | `/保研 experience` |
| 📖 专业课复习 | 基于湖大机械课程体系 + 简历项目，生成面试导向的知识点总结 | `/保研 review` |

### 📡 信息搜集 & 决策
| 功能 | 说明 | 命令 |
|------|------|------|
| 📡 通知聚合 | 18校夏令营/预推免通知自动抓取 + WebSearch 兜底 | `/保研 notice` |
| 🖥️ 通知 Dashboard | Web看板：搜索/筛选/排序/截止倒计时/来源标记 | `notices.html` |
| ⚖️ Offer 对比 | 8维对比分析 + 评分 + 建议 | `/保研 compare` |
| 📂 成果中心 | 一站式浏览所有生成文件，分类预览，一键复制 | `results.html` |

---

## 安装

```bash
git clone https://github.com/fndhwpoff/baoyan-skill.git ~/.claude/skills/保研skill
pip install -r ~/.claude/skills/保研skill/requirements.txt
```

---

## 快速使用

### 1️⃣ 材料准备
```
/保研 resume      # 翻译简历 + 生成面试题(含参考答案)
/保研 ps           # 生成个人陈述
/保研 email        # 搜索导师+生成联系邮件
/保研 recommend    # 生成推荐信草稿
```

### 2️⃣ 查通知 + 复习 + 决策
```
/保研 notice       # 抓取夏令营/预推免通知
/保研 review       # 专业课知识点复习（面试导向）
/保研 compare      # 对比多个Offer
```

### 3️⃣ 面试练习
```
/保研 practice     # 浏览器中英文面试练习（摄像头录制+实时AI点评）
/保研 mock         # AI模拟面试官（追问式）
/保研 experience   # 搜索各校面试经验
```

### 4️⃣ Web 页面
```bash
/保研 serve        # 启动本地 Web 服务
```

| 页面 | 地址 | 功能 |
|------|------|------|
| 🎥 面试练习 | `http://localhost:8765` | 中英文面试练习，摄像头录制，**实时AI点评** |
| 📡 通知 Dashboard | `http://localhost:8765/notices.html` | 通知聚合看板，截止倒计时，筛选排序 |
| 📂 成果中心 | `http://localhost:8765/results.html` | 所有生成文件分类浏览，一键预览+复制 (**NEW**) |
| 🤖 模拟面试官 | `http://localhost:8765/interviewer.html` | AI追问式面试对话展示 |

---

## 项目结构

```
保研skill/
├── SKILL.md                         # 入口文件 (v2.1)
├── prompts/                         # 提示词模板 (12个)
│   ├── resume_translate_en.md       #  简历翻译
│   ├── interview_questions_cn.md    #  中文面试题生成 (v2.1: 含参考答案)
│   ├── interview_questions_en.md    #  英文面试题生成 (v2.1: 含参考答案)
│   ├── notice_analysis.md           #  通知语义解析
│   ├── personal_statement_cn.md     #  个人陈述
│   ├── advisor_search.md            #  多导师搜索评估 (NEW v2.1)
│   ├── advisor_email_cn.md          #  联系导师邮件
│   ├── recommendation_letter_cn.md  #  推荐信
│   ├── course_review.md             #  专业课复习 (NEW v2.1)
│   ├── exam_prep.md                 #  笔试备考
│   ├── school_compare.md            #  Offer对比
│   └── experience_summary.md        #  面经提取
├── tools/                           # Python 工具 (4个)
│   ├── notice_scraper.py            #  通知爬虫
│   ├── question_store.py            #  题库管理
│   ├── experience_store.py          #  面经库管理
│   └── web_server.py                #  Web服务器 (v2.1升级)
├── config/schools.yaml              # 18校配置
├── data/                            # 持久化数据
│   ├── notices/                     #  通知缓存
│   ├── questions/                   #  题库
│   ├── experiences/                 #  面经库
│   ├── feedback/                    #  AI反馈
│   ├── exam_topics.json             #  笔试知识点
│   └── hnu_courses.json             #  湖大机械专业课体系 (NEW v2.1)
├── output/                          # 用户生成文件
│   ├── resume/  ├── questions/
│   ├── ps/      ├── email/
│   ├── recommend/  ├── exam/
│   └── compare/
└── web/                             # 前端页面 (4个)
    ├── index.html                   #  面试练习
    ├── notices.html                 #  通知Dashboard
    ├── results.html                 #  成果中心 (NEW v2.1)
    ├── interviewer.html             #  模拟面试官
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

## v2.1 更新内容（基于用户反馈）

相比 v2.0，v2.1 新增：

- 🆕 **成果展示门户** — `results.html` 一站式浏览所有生成文件，分类预览，一键复制
- 🆕 **专业课复习** — 替代笔试备考，基于湖南大学机械专业真实课程体系 + 面试导向
- 🆕 **多导师搜索** — 搜索3-5位候选导师，含研究方向、论文、风评来源标注
- 🆕 **题库扩容+参考答案** — 25-30题/语言，每题附带基于简历的具体参考答案
- 🆕 **实时AI反馈** — 无需离开练习页面，录音后网页轮询直接显示评分
- 🔧 **随机抽题** — 每次练习从题库随机抽取10道，避免重复

---

## 隐私

- ✅ 所有数据本地存储，不上传任何服务器
- ✅ 简历、面试题、练习录制均在你的电脑上
- ✅ 网页录制的视频仅存浏览器内存，关闭即消失
- ✅ 语音转写使用浏览器内置 Web Speech API（Chrome/Edge）
- ✅ 通知爬虫仅读取公开网页

---

## License

MIT © [fndhwpoff](https://github.com/fndhwpoff)
