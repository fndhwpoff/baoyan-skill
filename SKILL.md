---
name: 保研skill
description: >
  保研全流程助手 v2.1：简历翻译 + 中英文面试问题(含参考答案) + 夏令营/预推免通知聚合 + 面试口语练习(中/英) +
  个人陈述生成 + 多导师搜索推荐 + 推荐信草稿 + 专业课知识点复习 + Offer对比 + AI面试反馈 + 模拟面试官 + 面经库 +
  成果展示门户。
  触发词：保研、夏令营、预推免、简历翻译、面试问题、面试练习、机械保研。
argument-hint: "[resume | notice | interview | practice | ps | email | recommend | exam | compare | feedback | mock | experience]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, WebFetch, WebSearch
version: 2.1.0
---

# 保研 Skill v2.0 — 机械工程保研全流程助手

## 快速命令参考

| 命令 | 功能 | 说明 |
|------|------|------|
| `/保研 resume` | 简历翻译 + 面试题生成 | 中文简历→英文简历+中英文面试题 |
| `/保研 ps` | 个人陈述生成 | 定制化 1500-2000 字中文个人陈述 |
| `/保研 email` | 联系导师邮件 | 生成得体学术联系邮件 |
| `/保研 recommend` | 推荐信草稿 | 学术型/竞赛型推荐信 |
| `/保研 notice` | 通知聚合 | 18 校夏令营/预推免通知抓取+WebSearch |
| `/保研 review` | 专业课知识点复习 | 基于湖大课程体系+简历项目的面试专业课复习 |
| `/保研 compare` | Offer 对比 | 8 维对比分析 + 建议 |
| `/保研 practice` | 面试口语练习 | 浏览器端中英文面试练习 |
| `/保研 feedback` | AI 面试反馈 | 语音转写→AI评估 |
| `/保研 mock` | AI 模拟面试官 | 对话式追问面试 |
| `/保研 experience` | 面经搜索 | 搜索+结构化存储各校面经 |
| `/保研 serve` | 启动 Web 服务 | 启动本地 Web 服务 |
| `/保研 help` | 帮助 | 显示本帮助信息 |

## 工具使用规则

| 任务 | 工具 |
|------|------|
| 读取简历文件 | `Read` |
| 生成文本内容 | Claude 原生能力（参考 prompts/） |
| 保存文件 | `Write` |
| 通知抓取 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py` |
| WebSearch 兜底 | `WebSearch` + `python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py --action merge-websearch` |
| 面试题管理 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/question_store.py` |
| 面经管理 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/experience_store.py` |
| 启动 Web 服务 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/web_server.py` |
| 通知语义解析 | `WebFetch` |

---

## 功能一：简历翻译 + 面试题生成（/保研 resume）

### Step 1：接收简历
```
请提供你的中文简历，可以：
  [A] 直接粘贴文本
  [B] 上传文件（PDF/图片/Word/TXT）
  [C] 告诉我简历的文件路径
```

### Step 2：翻译英文简历
参考 `${CLAUDE_SKILL_DIR}/prompts/resume_translate_en.md`，输出到 `output/resume/`

### Step 3：生成中文面试问题
参考 `${CLAUDE_SKILL_DIR}/prompts/interview_questions_cn.md`，15-20 题，输出到 `output/questions/`

### Step 4：生成英文面试问题
参考 `${CLAUDE_SKILL_DIR}/prompts/interview_questions_en.md`，8-12 题，输出到 `output/questions/`

### Step 5：保存到题库（可选）
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/question_store.py --action save --file output/questions/interview_en_{timestamp}.md --session {姓名}_2026保研
```
（中文问题同理保存）

---

## 功能二：个人陈述生成（/保研 ps）

参考 `${CLAUDE_SKILL_DIR}/prompts/personal_statement_cn.md`

1. 询问：目标学校、目标专业方向、字数偏好（1500/1800/2000）、侧重点（科研为主/全面发展）
2. 基于简历内容生成 5 段式个人陈述（学术背景→科研经历→研究兴趣→择校理由→未来规划）
3. 输出到 `output/ps/ps_{timestamp}.md`

---

## 功能三：导师搜索与联系（/保研 email）

### Step 1：搜索多位候选导师
参考 `${CLAUDE_SKILL_DIR}/prompts/advisor_search.md`：
1. WebSearch 目标学校学院官网师资页面
2. 搜索科研产出（Google Scholar / CNKI）
3. 搜索导师风评（知乎/导师评价网，**必须标注来源和时效**）
4. 输出 **3-5 位**候选导师，含研究方向、论文、匹配度、风格信息
5. 如果没有找到风评，诚实标注"未找到"，建议通过学长学姐了解

### Step 2：学生选择后生成邮件
参考 `${CLAUDE_SKILL_DIR}/prompts/advisor_email_cn.md`：
1. 基于学生选择的导师，生成 300-500 字学术邮件
2. 含具体论文引用、匹配度展示、礼貌措辞
3. 输出到 `output/email/email_{school}_{advisor}_{timestamp}.md`

---

## 功能四：推荐信草稿（/保研 recommend）

参考 `${CLAUDE_SKILL_DIR}/prompts/recommendation_letter_cn.md`

1. 询问：推荐人类型（学术型/竞赛型）、希望突出的特质或具体事例
2. 以教授视角生成 500-800 字推荐信，[待补充] 标记需填写处
3. 输出到 `output/recommend/recommend_{type}_{timestamp}.md`

---

## 功能五：夏令营/预推免通知聚合（/保研 notice）

### Step 1：确定查询范围
```
[A] 全部学校（18 所）[B] 指定学校 [C] 仅查看缓存
```

### Step 2：运行爬虫
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py --school {all | 上交,浙大} --output data/notices/index.json {--refresh}
```

### Step 3：WebSearch 兜底
读取 `data/notices/index.json`，找出 `scraped: false` + `needs_websearch: true` 的学校，对每个失败学校用 **WebSearch**：
```
"[学校名] 机械 [学院名] 夏令营 2026 通知"
```
从搜索结果提取结构化通知，写入缓存：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py --action merge-websearch --school 西交 --data '[{...}]'
```

### Step 4：汇总展示
按截止日期排序表格展示。Dashboard 查看: `http://localhost:8765/notices.html`

---

## 功能六：专业课知识点复习（/保研 review）

参考 `${CLAUDE_SKILL_DIR}/prompts/course_review.md` 和 `data/hnu_courses.json`（湖南大学机械专业实际课程体系）

1. 读取简历，识别涉及的专业课领域
2. 从课程体系中提取相关知识点的 **面试重点**（不是笔试刷题，而是面试问答准备）
3. 按项目组织：每个项目→可能被追问的专业课知识→核心概念→回答框架
4. 包含跨课程综合问答和复习建议
5. 输出到 `output/exam/review_{timestamp}.md`

---

## 功能七：Offer 对比分析（/保研 compare）

参考 `${CLAUDE_SKILL_DIR}/prompts/school_compare.md`

1. 询问：2-5 所学校/Offer 信息
2. 8 维评分（学术/导师/方向/地点/就业/奖助/环境/毕业要求）
3. 生成对比表 + 雷达图描述 + 优劣总结 + 综合建议
4. 输出到 `output/compare/compare_{timestamp}.md`

---

## 功能八：面试口语练习（/保研 practice）

启动本地 Web 服务，在浏览器中进行中/英文面试练习。

### Step 1：启动服务
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/web_server.py --port 8765
```

### Step 2：浏览器打开
- 面试练习: `http://localhost:8765`
- 通知看板: `http://localhost:8765/notices.html`
- 模拟面试: `http://localhost:8765/interviewer.html`

### 功能特性
- 🌐 中/英文模式切换（点击页面顶部按钮）
- 📹 摄像头录制 + 回放
- ⏱️ 30 秒准备 + 90 秒作答
- 🔒 隐私安全，所有数据在本地浏览器
- 🤖 AI 点评按钮（录制后点击，语音转写→AI评估）

---

## 功能九：AI 面试反馈（/保研 feedback）

1. 在面试练习页点击"🤖 AI 点评"，获得 Session ID
2. 用户运行 `/保研 feedback`，Claude 读取反馈数据文件
3. 从三个维度评估：
   - **内容质量**（1-10）：观点完整性、论据支撑、专业深度
   - **语言流利度**（1-10）：表达流畅、用词准确、语法
   - **逻辑结构**（1-10）：结构清晰、论证有序、回答组织
4. 给出综合评分和改进建议
5. 读取的文件: `data/feedback/feedback_{session_id}.json`

---

## 功能十：AI 模拟面试官（/保研 mock）

1. 启动 Web 服务（如未启动）
2. Claude 扮演面试官，web 页面显示对话记录
3. 面试模式：提问→用户回答→追问(3-4轮)→下一题→综合评估
4. 会话数据存储在 `data/interview_session_{id}.json`
5. 面试完成后给出综合评估

页面: `http://localhost:8765/interviewer.html`

---

## 功能十一：面试经验搜索（/保研 experience）

1. 询问目标学校（如"上交"、"浙大"）或"全部"
2. WebSearch: `"[学校名] 机械 保研 面试经验 2025 2026"`
3. 从知乎/CSDN/保研论坛提取结构化面经
4. 保存到经验库：
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/experience_store.py --action save --school 上交 --year 2026 --data '{...}'
```
5. 也可用 `--action list` / `--action export` 查看和导出

---

## 管理命令

| 命令 | 说明 |
|------|------|
| `/保研 list-questions` | 列出题库 |
| `/保研 list-notices` | 列出通知缓存 |
| `/保研 clear-notices` | 清除通知缓存 |
| `/保研 serve` | 启动 Web 服务 |
| `/保研 help` | 帮助 |

---

## 项目结构

```
保研skill/
├── SKILL.md                       # 本文件 (v2.0)
├── prompts/                       # 提示词模板 (10个)
│   ├── resume_translate_en.md     # 英文简历翻译
│   ├── interview_questions_cn.md  # 中文面试题生成
│   ├── interview_questions_en.md  # 英文面试题生成
│   ├── notice_analysis.md         # 通知语义解析
│   ├── personal_statement_cn.md   # 个人陈述 (NEW)
│   ├── advisor_email_cn.md        # 联系导师邮件 (NEW)
│   ├── recommendation_letter_cn.md # 推荐信 (NEW)
│   ├── exam_prep.md               # 笔试备考 (NEW)
│   ├── school_compare.md          # Offer对比 (NEW)
│   └── experience_summary.md      # 面经提取 (NEW)
├── tools/                         # Python 工具 (4个)
│   ├── notice_scraper.py          # 通知爬虫 + WebSearch合并
│   ├── question_store.py          # 题库管理
│   ├── experience_store.py        # 面经库管理 (NEW)
│   └── web_server.py              # Web服务 (v2升级)
├── config/schools.yaml            # 18校配置
├── data/                          # 持久化数据
│   ├── notices/index.json
│   ├── questions/index.json
│   ├── experiences/index.json     # (NEW)
│   ├── feedback/                  # (NEW)
│   └── exam_topics.json           # (NEW)
├── output/                        # 输出文件
│   ├── resume/     ├── questions/
│   ├── ps/         ├── email/       # (NEW)
│   ├── recommend/  ├── exam/        # (NEW)
│   └── compare/                    # (NEW)
└── web/                           # 前端页面
    ├── index.html                 # 面试练习 (支持中英文)
    ├── notices.html               # 通知Dashboard
    ├── interviewer.html           # 模拟面试官 (NEW)
    ├── css/style.css
    └── js/ (app.js, camera.js, question_loader.js)
```
