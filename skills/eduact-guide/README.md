# 基础教育 skill（eduact-guide）

让 AI 助手照《高性价比基础教育指南》回答具体问题：课上怎么教、复习怎么安排、家长该怎么陪、学校人财物先投什么、哪些流行做法是迷思。

它做的事只有一件：**先把相关条目从正文里查出来，再按证据等级和成本排序回答**，每条注明出自第几篇第几条。查不到就说查不到，不凭记忆编数字。

规则全在 [SKILL.md](SKILL.md) 里，两个工具共用同一个文件，不维护两份。

## 装到 Claude Code

在本仓库里开 Claude Code，不用装——`.claude/skills/eduact-guide/` 已经指向这份规则。

想在任何目录下都能用，复制到个人 skill 目录：

```bash
mkdir -p ~/.claude/skills/eduact-guide && curl -fsSL -o ~/.claude/skills/eduact-guide/SKILL.md "https://raw.githubusercontent.com/musicer03/eduact/main/skills/eduact-guide/SKILL.md"
```

之后直接问「提问没人理怎么办」「该不该按成绩排座位」「按学习风格分组有用吗」就会触发；也可以显式说「用 eduact-guide 回答」。

## 装到 Codex

在本仓库里开 Codex，不用装——根目录的 `AGENTS.md` 已经把它指出来了。

想在任何目录下都能用，复制到 Codex 的个人 skill 目录 `~/.agents/skills`：

```bash
mkdir -p ~/.agents/skills/eduact-guide && curl -fsSL -o ~/.agents/skills/eduact-guide/SKILL.md "https://raw.githubusercontent.com/musicer03/eduact/main/skills/eduact-guide/SKILL.md"
```

之后直接问问题就会按描述自动触发，也可以输入 `$eduact-guide` 显式调用。注意是 `$` 不是 `/`，新版 Codex 输入 `/eduact-guide` 会报 `Unrecognized command`。没出现就重启一次 Codex。

旧版 Codex 还没有 skill，只能用自定义提示词：把文件放到 `~/.codex/prompts/eduact-guide.md`，再用 `/eduact-guide` 调用。Codex 已宣布弃用这套写法（[openai/codex#10848](https://github.com/openai/codex/issues/10848)），新版用上面的 skill 装法。

## 正文从哪来

本地有这个仓库就读本地的 `book/`；没有就现取：

```bash
git clone --depth 1 https://github.com/musicer03/eduact.git "${TMPDIR:-/tmp}/eduact"
```

整本几 MB，浅克隆一次几秒。取不到网络就如实说取不到，不替代正文。

不想装任何东西？打开[在线检索页](https://musicer03.github.io/eduact/)按条件筛条目，内容与正文同源。

## 改动须知

SKILL.md 里不留任何会跟着正文漂的清单和数值：篇的清单去读 README 的「这本书想回答的问题」表，条目格式以正文为准。所以增删条目、调篇序都不用动这个目录；只有编排逻辑（等级口径、四维记账、EEF 月数口径）变化时才需要同步改。
