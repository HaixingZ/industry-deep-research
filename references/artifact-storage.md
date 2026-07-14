# Artifact 存储

所有工作状态应保存为 markdown 文件。

## 运行目录

为每份报告创建一个独立目录：

```text
report_runs/<slug>/
```

使用包含主题和日期的简短缩写，例如：

```text
report_runs/ai-chip-packaging-260326/
```

## 文件序列

在运行目录内，保存编号文件，以便运行可以干净地恢复：

```text
01-research-brief.md
02-search-plan.md
03-source-index.md
04-storyline-packet.md
05-report-v1.md
06-review-v1.md
07-follow-up-search-v1.md
08-report-v2.md
09-review-v2.md
...
run-status.md
final-report.md
evidence-gap-log.md
search-records/
  主题-YYMMDD.md
```

并非每次运行都需要所有文件，但编号应保持稳定。

## run-status.md

断点恢复的核心文件。当路由为 `blocked` 或会话中断时写入运行目录。

记录内容：
- 当前阶段（正在执行流程的哪一步）
- 已完成项（哪些 artifact 已产出）
- 阻塞项（哪些信息无法获取及原因）
- 待整合材料（用户提供了但尚未整合的材料）
- 下一步（新会话应从哪里开始）

新会话读取此文件 + 最新评审文件继续工作。恢复后使用完整质量标准。

## search-records/ 子目录

每轮搜索产出一个存档文件，保存在运行目录的 `search-records/` 下。

命名格式：`主题-YYMMDD.md`

格式规范参见 `references/search-record-format.md`。

不要覆盖搜索记录。在 `03-source-index.md` 的 `## Search Records` 下链接它们。

## 轮次递增规则

永远不要覆盖之前的评审轮次。如果运行循环，递增版本号：
- `06-review-v1.md` → `09-review-v2.md`
- `07-follow-up-search-v1.md` → `10-follow-up-search-v2.md`
- `05-report-v1.md` → `08-report-v2.md`

这样可以保持推理轨迹可检查，并使长时间运行的工作可恢复。
