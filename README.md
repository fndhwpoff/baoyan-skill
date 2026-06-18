# 保研 Skill v2.3

> 机械工程保研全流程助手：从材料准备、信息搜集到面试练习，一站式搞定  
> Claude Code Skill · 开源 · 零数据上传

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)]()

---

## 功能一览

### 📝 材料准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 🇬🇧 简历翻译 | 中文简历 → 专业英文简历（含机械工程术语表） | `/保研 resume` |
| 📄 个人陈述 | 定制化 1500-2000 字中文个人陈述（5段式），**按学校定制** | `/保研 ps` |
| ✉️ 导师搜索与邮件 | 先选学校 → 搜多位导师(含风评) → **7校专属模板**生成邮件 | `/保研 email` |
| 📨 推荐信草稿 | 教授视角推荐信（学术型/竞赛型），**按学校风格定制** | `/保研 recommend` |

### 🎤 面试准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 📋 面试题生成 | 25-30题/语言 + 参考答案（基于简历经历），随机抽10道练习 | `/保研 resume` |
| 🎥 口语练习 | 浏览器端中英文面试练习，摄像头录制+**自动AI点评** | `/保研 practice` |
| 🤖 AI 面试反馈 | 录音后自动提交→2秒轮询→**页面直接显示三维度评分** | 练习页内置 |
| 🎓 AI 模拟面试官 | 对话式追问面试，3-4轮追问/题 → 综合评估 | `/保研 mock` |
| 📚 面经搜索 | 搜索知乎/保研论坛面经，结构化存储 | `/保研 experience` |
| 📖 专业课复习 | 基于湖大机械课程体系 + 简历项目，面试导向的知识点总结 | `/保研 review` |

### 📡 信息搜集 & 决策
| 功能 | 说明 | 命令 |
|------|------|------|
| 📡 通知聚合 | 18校夏令营/科研营/预推免自动抓取 + WebSearch兜底，**优先2026** | `/保研 notice` |
| 🖥️ 通知 Dashboard | Web看板：截止倒计时/筛选排序/来源标记 | `notices.html` |
| ⚖️ Offer 对比 | 8维对比分析 + 评分 + 建议 | `/保研 compare` |
| 📂 成果中心 | 一站式浏览，**网页版预览 + 打印PDF**，分类查看，一键复制 | `results.html` |

---

## 安装

```bash
git clone https://github.com/fndhwpoff/baoyan-skill.git ~/.claude/skills/保研skill
pip install -r ~/.claude/skills/保研skill/requirements.txt
pip install markdown  # PDF生成依赖
```

---

## 快速使用

### 1️⃣ 材料准备
```
/保研 resume      # 翻译简历 + 生成面试题(含参考答案)
/保研 ps           # 生成个人陈述（按目标学校定制）
/保研 email        # 搜索导师 + 按学校模板生成邮件
/保研 recommend    # 生成推荐信草稿
```

### 2️⃣ 查通知 + 复习 + 决策
```
/保研 notice       # 抓取夏令营/科研营/预推免通知
/保研 review       # 专业课知识点复习（基于湖大课程）
/保研 compare      # 对比多个Offer
```

### 3️⃣ 面试练习
```
/保研 practice     # 浏览器面试练习（自动AI点评）
/保研 mock         # AI模拟面试官
/保研 experience   # 搜索各校面试经验
```

### 4️⃣ Web 页面（`/保研 serve` 启动）
| 页面 | 地址 | 功能 |
|------|------|------|
| 🏠 总门户 | `/` | 全部功能入口，统计概览 |
| 🎥 面试练习 | `/practice.html` | 中英文面试，摄像头录制，**自动AI点评** |
| 📡 通知看板 | `/notices.html` | 截止倒计时，筛选排序，来源标记 |
| 📂 成果中心 | `/results.html` | 文件浏览，**网页版+PDF**，一键复制 |
| 🤖 模拟面试 | `/interviewer.html` | AI追问式对话面试 |

**自动AI反馈**：启动时加 `--watch-feedback` 自动处理反馈队列：
```bash
python tools/web_server.py --port 8765 --watch-feedback
```

---

## 项目结构

```
保研skill/
├── SKILL.md                         # 入口文件 (v2.3)
├── prompts/                         # 提示词模板 (12个)
│   ├── resume_translate_en.md       #  简历翻译
│   ├── interview_questions_cn.md    #  中文面试题 (含参考答案)
│   ├── interview_questions_en.md    #  英文面试题 (含参考答案)
│   ├── notice_analysis.md           #  通知语义解析
│   ├── personal_statement_cn.md     #  个人陈述
│   ├── advisor_search.md            #  多导师搜索
│   ├── advisor_email_cn.md          #  联系导师邮件
│   ├── recommendation_letter_cn.md  #  推荐信
│   ├── course_review.md             #  专业课复习
│   ├── exam_prep.md                 #  笔试备考
│   ├── school_compare.md            #  Offer对比
│   └── experience_summary.md        #  面经提取
├── tools/                           # Python 工具 (6个)
│   ├── notice_scraper.py            #  通知爬虫 (v2.2扩展关键词)
│   ├── question_store.py            #  题库管理
│   ├── experience_store.py          #  面经库管理
│   ├── web_server.py                #  Web服务器 (v2.3: PDF+自动反馈)
│   ├── pdf_generator.py             #  MD→HTML转换 (NEW v2.3)
│   └── feedback_worker.py           #  自动AI反馈 (NEW v2.3)
├── config/schools.yaml              # 18校配置 (v2.2修正URL)
├── data/                            # 持久化数据 (7个)
│   ├── school_templates.json        #  7校专属模板 (NEW v2.3)
│   ├── hnu_courses.json             #  湖大专业课体系
│   ├── exam_topics.json             #  笔试知识点
│   ├── notices/  questions/  experiences/  feedback/
├── output/                          # 用户生成文件 (9个目录 + HTML版)
├── web/                             # 前端页面 (5个, 统一导航)
│   ├── index.html                   #  总门户
│   ├── practice.html                #  面试练习 (v2.2自动反馈)
│   ├── notices.html                 #  通知Dashboard
│   ├── results.html                 #  成果中心 (v2.3网页版+PDF)
│   └── interviewer.html             #  模拟面试官
└── requirements.txt
```

---

## 覆盖学校

| 层次 | 学校 |
|------|------|
| C9 | 清华、北大、上交、浙大、西交、哈工大、哈工深、中科大 |
| 机械强校985 | 同济、华科、北航、北理、大工、天大、西工大、东大、华工、重大 |

共 18 所。7 所学校有专属邮件/PS/推荐信模板（清华/上交/浙大/华科/哈工大/北航/同济）。

> ⚠️ 部分学校通知页 URL 可能失效，遇到抓取失败时自动使用 WebSearch 兜底，并优先展示 2025-2026 年最新通知。

---

## 更新日志

### v2.3 (2026.06)
- 🆕 **HTML/PDF生成** — pdf_generator.py 批量转换，成果中心一键打开
- 🆕 **自动AI反馈** — feedback_worker.py 规则引擎，支持 --watch 持续监控
- 🆕 **分学校模板** — 清华/上交/浙大/华科/哈工大/北航/同济 7 校专属风格
- 🆕 **子页面统一** — 全部5个页面统一导航栏设计
- 🔧 **爬虫扩展** — 科研营/学术营/开放日关键词，URL修正，2026优先

### v2.2 (2026.06)
- 🆕 网页重设计 + PDF打印 + AI反馈Web化 + 爬虫关键词扩展

### v2.1 (2026.06)
- 🆕 成果中心 + 专业课复习 + 多导师搜索 + 题库参考答案 + 实时反馈

### v2.0 (2026.06)
- 🆕 个人陈述/导师邮件/推荐信/笔试备考/Offer对比/AI反馈/模拟面试/面经/中文模式/移动端

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
