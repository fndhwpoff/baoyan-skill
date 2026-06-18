# 保研 Skill

> 机械工程保研全流程助手：英文简历 + 面试题库 + 通知聚合 + 口语练习

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)

## 功能

| 功能 | 说明 | 命令 |
|------|------|------|
| 📝 简历翻译 | 中文简历 → 专业英文简历 | `/保研 resume` |
| 🎤 面试题生成 | 基于简历生成中英文面试问题 | 同上 |
| 📢 通知聚合 | 抓取各校机械学院夏令营/预推免通知 | `/保研 notice` |
| 🎥 口语练习 | 摄像头模拟英文面试 | `/保研 practice` |

## 安装

```bash
# 安装到此项目
mkdir -p .claude/skills
cp -r "D:/Claude/保研skill" .claude/skills/保研skill

# 或安装到全局（所有项目可用）
cp -r "D:/Claude/保研skill" ~/.claude/skills/保研skill
```

### 依赖

```bash
pip install -r requirements.txt
```

## 快速使用

在 Claude Code 中输入：

### 1. 翻译简历 + 生成面试题
```
/保研 resume
```
然后按提示提供简历（粘贴/上传文件/指定路径），AI 会生成三份文件：
- `output/resume/` — 英文简历
- `output/questions/` — 中文面试题（15-20题）
- `output/questions/` — 英文面试题（8-12题）

### 2. 查夏令营/预推免通知
```
/保研 notice
```
自动抓取 18 所机械强校的最新通知，按截止日期排序展示。

### 3. 英文口语练习
```
/保研 practice
```
启动本地网页（`localhost:8765`），使用摄像头进行模拟英文面试。

## 项目结构

```
保研skill/
├── SKILL.md                    # 入口文件
├── prompts/                    # 提示词模板
├── tools/                      # Python 工具
├── config/schools.yaml         # 学校配置
├── data/                       # 数据存储
├── output/                     # 生成输出
└── web/                        # 英文练习网页
```

## 覆盖学校

| 层次 | 学校 |
|------|------|
| C9 | 清华、北大、上交、浙大、西交、哈工大、哈工深、中科大 |
| 机械强校985 | 同济、华科、北航、北理、大工、天大、西工大、东大、华工、重大 |

共 18 所。可在 `config/schools.yaml` 中增删。

## 隐私

- 所有数据本地存储，不上传任何服务器
- 简历、面试题、练习录制均在你自己的电脑上
- 网页录制的视频仅存浏览器内存，关闭即消失

## License

MIT
