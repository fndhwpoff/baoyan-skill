---
name: baoyan-skill
description: >
  机械工程保研全流程助手 v3.0。Use when Codex or Claude Code needs to help with 保研/推免/夏令营/预推免 workflows:
  简历翻译, 中英文面试问题与参考答案, 个人陈述, 导师搜索与联系邮件, 推荐信草稿, 专业课面试复习,
  夏令营/预推免通知聚合, 面试口语练习, 面经搜索, Offer 对比, 本地 Web 门户与成果展示。
  触发词：保研、夏令营、预推免、简历翻译、面试问题、面试练习、机械保研。
allowed-tools: Read, Write, Edit, Bash, WebFetch, WebSearch
---

# 保研 Skill v3.0

## 平台兼容

- Codex: 依靠 frontmatter 的 `name` 和 `description` 自动触发；工具命令优先用 `python`。
- Claude Code: 继续用 `/保研 <command>` 形式调用；本文件保留命令表和执行流程。
- 技能目录: Claude Code 中通常是 `${CLAUDE_SKILL_DIR}`；Codex 中使用当前 skill 根目录或仓库根目录。
- 网络信息: 通知、导师、面经等会变化，涉及最新信息时必须搜索并标注来源与日期。

## 快速命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `/保研 resume` | 简历翻译 + 面试题生成 | 中文简历转英文简历，并生成中英文面试题 |
| `/保研 ps` | 个人陈述 | 生成 1500-2000 字中文个人陈述 |
| `/保研 email` | 导师搜索与邮件 | 搜索候选导师并生成联系邮件 |
| `/保研 recommend` | 推荐信草稿 | 学术型/竞赛型推荐信草稿 |
| `/保研 notice` | 通知聚合 | 抓取 18 校夏令营/预推免通知，失败时搜索兜底 |
| `/保研 review` | 专业课复习 | 基于湖大机械课程体系和简历项目生成面试复习材料 |
| `/保研 compare` | Offer 对比 | 8 维对比分析与建议 |
| `/保研 practice` | 面试练习 | 启动浏览器端中英文面试练习 |
| `/保研 experience` | 面经搜索 | 搜索并结构化存储各校面经 |
| `/保研 serve` | Web 服务 | 启动本地门户、通知看板、成果中心 |
| `/保研 help` | 帮助 | 显示命令说明 |

## 资源地图

| 任务 | 主要资源 |
|------|------|
| 简历翻译 | `prompts/resume_translate_en.md` |
| 中文面试题 | `prompts/interview_questions_cn.md` |
| 英文面试题 | `prompts/interview_questions_en.md` |
| 个人陈述 | `prompts/personal_statement_cn.md`, `data/school_templates.json` |
| 导师搜索与邮件 | `prompts/advisor_search.md`, `prompts/advisor_email_cn.md`, `data/school_templates.json` |
| 推荐信 | `prompts/recommendation_letter_cn.md` |
| 通知分析 | `tools/notice_scraper.py`, `prompts/notice_analysis.md`, `config/schools.yaml` |
| 专业课复习 | `prompts/course_review.md`, `data/hnu_courses.json`, `data/exam_topics.json` |
| Offer 对比 | `prompts/school_compare.md` |
| 面经 | `prompts/experience_summary.md`, `tools/experience_store.py` |
| Web 门户 | `tools/web_server.py`, `web/` |

## 工作流

### `/保研 resume`

1. 获取简历文本或文件路径。
2. 按 `prompts/resume_translate_en.md` 生成英文简历，保存到 `output/resume/`。
3. 按 `prompts/interview_questions_cn.md` 生成 15-20 道中文题，保存到 `output/questions/`。
4. 按 `prompts/interview_questions_en.md` 生成 8-12 道英文题，保存到 `output/questions/`。
5. 可选：保存题库。

```bash
python tools/question_store.py --action save --file output/questions/interview_en_{timestamp}.md --session {姓名}_2026保研
```

### `/保研 ps`

1. 询问目标学校、目标专业方向、字数偏好、材料侧重点。
2. 结合简历和 `data/school_templates.json` 生成 5 段式个人陈述。
3. 保存到 `output/ps/ps_{school}_{timestamp}.md`。

### `/保研 email`

1. 搜索目标学校学院官网师资页面和导师近期成果。
2. 如搜索导师风评，必须标注来源、日期和可信度；找不到就写明未找到。
3. 输出 3-5 位候选导师，包含方向、代表成果、匹配度、信息来源。
4. 用户选择导师后，按 `prompts/advisor_email_cn.md` 生成邮件，保存到 `output/email/`。

### `/保研 recommend`

1. 询问推荐人类型、推荐重点和具体事例。
2. 以教授视角生成 500-800 字草稿，用 `[待补充]` 标记真实信息缺口。
3. 保存到 `output/recommend/`。

### `/保研 notice`

1. 确定范围：全部学校、指定学校或只看缓存。
2. 运行爬虫。

```bash
python tools/notice_scraper.py --school all --output data/notices/index.json --refresh
```

3. 对 `scraped: false` 或 `needs_websearch: true` 的学校使用 WebSearch 兜底。
4. 合并搜索结果时传入结构化 JSON，并保留来源链接。

```bash
python tools/notice_scraper.py --action merge-websearch --school 西交 --data '[{"title":"...","url":"..."}]'
```

### `/保研 review`

1. 读取简历，识别项目涉及的课程领域。
2. 从 `data/hnu_courses.json` 提取相关知识点。
3. 按“项目 -> 可能追问 -> 核心概念 -> 回答框架”组织。
4. 保存到 `output/exam/`。

### `/保研 compare`

1. 询问 2-5 个学校或 Offer 的关键信息。
2. 从学术、导师、方向、地点、就业、奖助、环境、毕业要求 8 维评分。
3. 输出对比表、雷达图文字描述、风险点和建议，保存到 `output/compare/`。

### `/保研 practice` 或 `/保研 serve`

启动本地 Web 服务：

```bash
python tools/web_server.py --port 8765
```

页面：

- 总门户: `http://localhost:8765/`
- 面试练习: `http://localhost:8765/practice.html`
- 通知看板: `http://localhost:8765/notices.html`
- 成果中心: `http://localhost:8765/results.html`

### `/保研 experience`

1. 询问目标学校或范围。
2. 搜索公开面经，优先近两年，并记录来源。
3. 按 `prompts/experience_summary.md` 结构化提取。
4. 保存到经验库。

```bash
python tools/experience_store.py --action save --school 上交 --year 2026 --data '{...}'
```

## 注意事项

- 不要编造导师论文、通知日期、报名截止时间或风评；不确定时明确说明。
- 通知抓取依赖公开网页，部分学校会失败；失败时使用 WebSearch 兜底并写入缓存。
- Web 练习页当前提供录制与回放，不再承诺独立的模拟面试官页面。
- 用户生成内容默认写入 `output/`，运行缓存默认写入 `data/`。

## 项目结构

```text
保研skill/
├── SKILL.md
├── README.md
├── prompts/                 # 12 个提示词模板
├── tools/                   # 爬虫、题库、面经、Web 服务、HTML 生成等工具
├── config/schools.yaml      # 18 校配置
├── data/                    # 模板、课程体系、运行缓存
├── output/                  # 用户生成材料
└── web/                     # 总门户、练习页、通知看板、成果中心
```
