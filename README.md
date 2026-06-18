# 保研 Skill v3.0

> 机械工程保研全流程助手：材料准备 · 信息搜集 · 面试练习，一站搞定  
> Claude Code Skill · 开源 · 零数据上传

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)]()

---

## &#127760; 总网站

启动本地服务后访问 **`http://localhost:8765`**，一站式管理保研全流程：

```
/保研 serve          # 启动服务
```

| 页面 | 地址 | 功能亮点 |
|------|------|----------|
| &#127968; **总门户** | `/` | Hero大屏统计 · 全部功能卡片 · 一键跳转各工具 |
| &#127916; 面试练习 | `/practice.html` | 中英文切换 · 摄像头录制 · 回放复盘 |
| &#128225; 通知看板 | `/notices.html` | 18校通知 · 截止倒计时 · 一键刷新 |
| &#128194; **成果中心** | `/results.html` | 7校全套材料 · 按学校分组 · HTML预览 · PDF打印 |

> 打开总网站即可看到全部功能入口，无需记忆多个地址。

---

## 功能一览

### 📝 材料准备（按学校定制）
| 功能 | 说明 | 命令 |
|------|------|------|
| 🇬🇧 简历翻译 | 中文简历 → 专业英文简历（含机械工程术语表） | `/保研 resume` |
| 📄 个人陈述 | 5段式定制化PS，**7校覆盖**（上交/清华/华科/浙大/哈工深/同济/西交） | `/保研 ps` |
| ✉️ 导师搜索与邮件 | 先选学校 → 搜多位导师(含风评来源) → 7校专属模板生成邮件 | `/保研 email` |
| 📨 推荐信草稿 | 教授视角推荐信（学术型/竞赛型），按学校风格定制 | `/保研 recommend` |

### 🎤 面试准备
| 功能 | 说明 | 命令 |
|------|------|------|
| 📋 面试题生成 | 25-30题/语言 + 参考答案（基于简历经历），随机抽10道练习 | `/保研 resume` |
| 🎥 面试练习 | 浏览器端中英文面试练习，摄像头录制+回放，**纯净体验** | `/保研 practice` |
| 📚 面经搜索 | 搜索知乎/保研论坛面经，结构化存储 | `/保研 experience` |
| 📖 专业课复习 | 湖大机械**10门核心课**知识点总结，面试导向 | `/保研 review` |

### 📡 信息搜集 & 决策
| 功能 | 说明 | 命令 |
|------|------|------|
| 📡 通知聚合 | 18校夏令营/科研营/预推免自动抓取 + WebSearch兜底，优先2026 | `/保研 notice` |
| 🖥️ 通知 Dashboard | Web看板：截止倒计时/筛选排序/来源标记 | `notices.html` |
| ⚖️ Offer 对比 | 8维对比分析 + 评分 + 建议 | `/保研 compare` |
| 📂 成果中心 | 19个文件，**按类型/按学校**双视图，HTML预览，打印PDF | `results.html` |

---

## 安装

```bash
git clone https://github.com/fndhwpoff/baoyan-skill.git ~/.claude/skills/保研skill
pip install -r ~/.claude/skills/保研skill/requirements.txt
pip install markdown
```

---

## 快速使用

### 1️⃣ 材料准备
```
/保研 resume      # 翻译简历 + 生成面试题(含参考答案)
/保研 ps           # 生成个人陈述（选目标学校）
/保研 email        # 搜索导师 + 按学校模板生成邮件
/保研 recommend    # 生成推荐信草稿
```

### 2️⃣ 查通知 + 复习
```
/保研 notice       # 抓取夏令营/科研营/预推免通知
/保研 review       # 专业课知识点复习（10门课程）
/保研 compare      # 对比多个Offer
```

### 3️⃣ 面试练习
```
/保研 practice     # 浏览器面试练习（摄像头录制+回放）
/保研 experience   # 搜索各校面试经验
```

### 4️⃣ Web 页面（`/保研 serve` 启动）
| 页面 | 地址 | 功能 |
|------|------|------|
| 🏠 总门户 | `/` | 全部功能入口，统计概览 |
| 🎥 面试练习 | `/practice.html` | 中英文面试，摄像头录制，纯净体验 |
| 📡 通知看板 | `/notices.html` | 截止倒计时，筛选排序，来源标记 |
| 📂 成果中心 | `/results.html` | 按类型/按学校双视图，HTML预览，打印PDF |

---

## 项目结构

```
保研skill/
├── SKILL.md                         # 入口文件
├── prompts/                         # 提示词模板 (13个)
│   ├── resume_translate_en.md
│   ├── interview_questions_cn.md    # 含参考答案
│   ├── interview_questions_en.md    # 含参考答案
│   ├── personal_statement_cn.md
│   ├── advisor_search.md            # 多导师搜索
│   ├── advisor_email_cn.md
│   ├── recommendation_letter_cn.md
│   ├── course_review.md             # 专业课复习
│   ├── school_compare.md
│   ├── exam_prep.md
│   ├── notice_analysis.md
│   ├── experience_summary.md
│   └── school_compare.md
├── tools/                           # Python 工具 (5个)
│   ├── notice_scraper.py            # 通知爬虫(科研营/夏令营等关键词)
│   ├── web_server.py                # Web服务器
│   ├── pdf_generator.py             # MD→HTML批量转换
│   ├── question_store.py            # 题库管理
│   └── experience_store.py          # 面经库管理
├── config/schools.yaml              # 18校配置
├── data/
│   ├── school_templates.json        # 7校专属邮件/PS模板
│   ├── hnu_courses.json             # 湖大10门专业课体系
│   ├── exam_topics.json
│   └── notices/  questions/  experiences/
├── output/                          # 用户生成文件 (7校PS+导师+复习)
├── web/                             # 前端 (4个页面, 统一导航)
│   ├── index.html                   # 总门户
│   ├── practice.html                # 面试练习
│   ├── notices.html                 # 通知Dashboard
│   └── results.html                 # 成果中心(双视图+HTML预览)
└── requirements.txt
```

---

## 覆盖学校

| 层次 | 学校 |
|------|------|
| C9 | 清华、北大、上交、浙大、西交、哈工大、哈工深、中科大 |
| 机械强校985 | 同济、华科、北航、北理、大工、天大、西工大、东大、华工、重大 |

18 所全覆盖。已生成**7校专属材料**（上交/清华/华科/浙大/哈工深/同济/西交），含个人陈述和导师列表。10 门专业课知识点覆盖面试高频考点。

---

## 更新日志

### v3.0 (2026.06)
- 🆕 **7校覆盖** — 新增浙大/哈工深/同济/西交 PS + 导师列表
- 🆕 **课程扩充** — 10门专业课（+微控制器/数值方法/互换性/制造装备）
- 🔧 **简化体验** — 移除AI评分，练习页纯净录制+回放
- 🔧 **页面合并** — 删除独立面试页，练习统一入口
- 🔧 **成果中心** — 按学校/按类型双视图

### v2.x (2026.06)
- HTML/PDF生成 · 自动AI反馈 · 分学校模板 · 子页面统一 · 爬虫扩展

### v1.0 (2026.06)
- 简历翻译 · 面试题生成 · 通知聚合 · 英文口语练习

---

## 隐私

- ✅ 所有数据本地存储，不上传任何服务器
- ✅ 网页录制仅存浏览器内存，关闭即消失
- ✅ 语音转写使用浏览器内置 Web Speech API（Chrome/Edge）
- ✅ 通知爬虫仅读取公开网页

---

## License

MIT © [fndhwpoff](https://github.com/fndhwpoff)
