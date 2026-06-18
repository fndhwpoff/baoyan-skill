---
name: 保研skill
description: >
  保研全流程助手：英文简历翻译 + 中英文面试问题生成 + 夏令营/预推免通知聚合 + 英文口语面试练习。
  触发词：保研、夏令营、预推免、简历翻译、面试问题、英文练习、机械保研。
argument-hint: "[resume | notice | interview | practice]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, WebFetch, WebSearch
version: 1.0.0
---

# 保研 Skill — 机械工程保研全流程助手

## 触发条件

当用户提到以下任意内容时启动：

| 触发方式 | 示例 |
|----------|------|
| 斜杠命令 | `/保研 resume`、`/保研 notice`、`/保研 interview`、`/保研 practice` |
| 自然语言 | "帮我翻译简历"、"生成英文简历"、"帮我准备面试"、"查夏令营通知"、"搜预推免"、"英文面试练习"、"模拟面试" |

---

## 工具使用规则

| 任务 | 工具 |
|------|------|
| 读取简历文件（PDF/图片/TXT/MD） | `Read` |
| 翻译简历、生成面试题 | Claude 原生能力（参考 prompts/） |
| 保存生成的文件 | `Write` |
| 批量抓取学校通知 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py` |
| 语义解析通知内容 | `WebFetch`（重点学校）/ Python scraper（全量） |
| 管理面试题 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/question_store.py` |
| 启动英文练习网页 | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/web_server.py` |

**基础目录**：所有输出文件写入 `./output/`（相对于本项目目录）。

---

## 功能一：简历翻译 + 面试题生成（/保研 resume）

### 触发
用户说"帮我翻译简历"、"生成面试问题"、"/保研 resume"、"帮我准备保研面试"

### 工作流

#### Step 1：接收简历
询问用户提供简历：
```
请提供你的中文简历，可以：
  [A] 直接粘贴文本
  [B] 上传文件（PDF/图片/Word/TXT）
  [C] 告诉我简历的文件路径
```

- 如果是文件路径 → 用 `Read` 工具读取
- 如果是粘贴 → 直接接收文本
- 如果是 PDF/图片 → 用 `Read` 工具读取（Claude 原生支持）

#### Step 2：翻译英文简历
参考 `${CLAUDE_SKILL_DIR}/prompts/resume_translate_en.md` 中的翻译规则：

- 保留所有事实内容，不做增删
- 将中文简历各部分映射为英文对应格式
- 正确处理机械工程专业术语（如"有限元分析" → "Finite Element Analysis (FEA)"）
- 保持 ATS 友好格式
- 以 Markdown 格式输出英文简历

写入 `output/resume/resume_en_{timestamp}.md`

#### Step 3：生成中文面试问题
参考 `${CLAUDE_SKILL_DIR}/prompts/interview_questions_cn.md` ：

- 角色扮演为机械工程保研面试官
- 根据简历内容生成 15-20 个中文问题
- 覆盖三个维度：
  1. **技术问题**：项目细节、科研方法、专业课程
  2. **行为问题**：团队协作、解决冲突、研究动机
  3. **通用问题**：自我介绍、优缺点、未来规划
- 每题附上"面试官想考察什么"和"回答提示"

写入 `output/questions/interview_cn_{timestamp}.md`

#### Step 4：生成英文面试问题
参考 `${CLAUDE_SKILL_DIR}/prompts/interview_questions_en.md` ：

- 生成 8-12 个英文问题
- 覆盖技术和行为维度
- 每题附考察点和回答提示
- 额外标注可能的追问

写入 `output/questions/interview_en_{timestamp}.md`

#### Step 5：保存到题库（可选）
询问用户是否将问题存入题库（供功能三使用）：
```
是否将面试题保存到题库？（保存后可用于英文口语练习）
  [Y] 保存
  [N] 仅导出文件
```

如果保存 → `python3 ${CLAUDE_SKILL_DIR}/tools/question_store.py --action save --file output/questions/interview_en_{timestamp}.md`

---

## 功能二：夏令营/预推免通知聚合（/保研 notice）

### 触发
用户说"查夏令营通知"、"搜预推免"、"/保研 notice"、"有哪些学校出通知了"

### 工作流

#### Step 1：确定查询范围
```
查询范围？
  [A] 全部学校（~15 所）
  [B] 指定学校（如：上交、浙大、华科）
  [C] 仅查看缓存（不重新抓取）
```

#### Step 2：运行爬虫
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/notice_scraper.py \
  --school {all | 上交,浙大,华科} \
  --output data/notices/index.json \
  {--refresh 如果需要强制刷新}
```

#### Step 3：补充语义解析
爬虫完成批量抓取后，对尚未确定截止日期和关键信息的学校，使用 `WebFetch` 工具直接读取原始页面，做语义级提取。

#### Step 4：汇总展示
按截止日期排序，以表格形式展示：

```markdown
| 学校 | 学院 | 类型 | 截止日期 | 关键要求 | 链接 |
|------|------|------|----------|----------|------|
| 上交 | 机械与动力工程学院 | 夏令营 | 2026-06-30 | GPA 3.5+ | [链接](...) |
| ...  | ...  | ...  | ...      | ...      | ...  |
```

同时写入 `data/notices/summary_{date}.md`。

---

## 功能三：英文口语练习（/保研 practice）

### 前置条件
题库中存在面试问题（运行过功能一并保存了英文问题）。

如果题库为空，自动引导用户先运行 `/保研 resume` 生成问题。

### 触发
用户说"英文口语练习"、"/保研 practice"、"模拟英文面试"、"练习面试"

### 工作流

#### Step 1：启动服务
```bash
python3 ${CLAUDE_SKILL_DIR}/tools/web_server.py --port 8765
```

#### Step 2：引导用户
```
英文面试练习已启动！请在浏览器打开：

  👉 http://localhost:8765

功能说明：
  - 摄像头模拟真实面试场景
  - 题目来自你的英文面试题库
  - 每题 30 秒准备 + 90 秒作答
  - 录制内容仅保存在你的浏览器中，不上传
  - 支持回放查看自己的表现

按 Ctrl+C 停止服务。
```

#### Step 3：网页端体验
网页详情参考 `web/assets/README.md`。

---

## 管理命令

| 命令 | 说明 |
|------|------|
| `/保研 list-questions` | 列出题库中所有问题 |
| `/保研 list-notices` | 列出缓存的通知 |
| `/保研 clear-notices` | 清除通知缓存 |
| `/保研 serve` | 启动英文练习网页 |
| `/保研 help` | 显示帮助信息 |

---

## 项目结构

```
保研skill/
├── SKILL.md                    # 本文件
├── prompts/                    # 提示词模板
│   ├── resume_translate_en.md
│   ├── interview_questions_cn.md
│   ├── interview_questions_en.md
│   └── notice_analysis.md
├── tools/                      # Python 工具
│   ├── notice_scraper.py
│   ├── question_store.py
│   └── web_server.py
├── config/
│   └── schools.yaml            # 学校配置
├── data/                       # 持久化数据
│   ├── notices/
│   └── questions/
├── output/                     # 用户面向输出
│   ├── resume/
│   └── questions/
└── web/                        # 英文练习网页
    ├── index.html
    ├── css/style.css
    └── js/
        ├── app.js
        ├── camera.js
        └── question_loader.js
```
