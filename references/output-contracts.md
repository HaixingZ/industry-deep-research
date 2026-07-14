# 输出契约

默认中文。保留原始文档标题为源语言。

---

## 搜索输出格式

### 搜索来源包格式

#### 1. 检索摘要

- `主题`:
- `地域/市场`:
- `时间范围`:
- `来源偏好`:
- `说明`:

#### 2. 必读来源

3 个或以上来源时使用紧凑表格。否则使用项目符号。

表格列：
- `标题`
- `机构/公众号`
- `日期`
- `类型`
- `访问`
- `价值`
- `官方页`
- `PDF`

访问标签：
- `official PDF`
- `official page`
- `wechat official account`
- `authorized distribution`
- `secondary mirror`

类型标签：
- `consulting report`
- `white paper`
- `broker research`
- `regulator/exchange`
- `company IR`
- `association/standard`
- `wechat official account`
- `platform research`

#### 3. 补充来源

仅纳入有相邻证据、替代角度或支持性数据的来源。

#### 4. 缺口与受限来源

说明：
- 仅存在落地页
- 仅找到二次转载
- 请求的来源类型在该主题下似乎稀缺
- 信息无法通过公开渠道获取

#### 5. 下一步检索

仅在第一轮检索不完整时提供 2-5 条精准的下步方向。

#### 选择规则

- 以最强的原件 PDF 引领，而非最有名的品牌
- 优先 5-10 条高信号项而非冗长的弱列表
- 积极去重
- 如用户明确要求 PDF 原件，在项目符号中将 `PDF` 置于 `官方页` 之前
- 如无公开 PDF，标注 `无公开 PDF，仅官方页面`

#### 项目符号格式

列表较短时使用：

- `标题` | 机构/公众号 | 日期 | 类型 | 访问
  `价值`: 一句话
  `官方页`: URL
  `PDF`: URL 或 `无公开 PDF`

---

## 报告 Artifact 格式

### Artifact 1 — Research Brief

```md
# Research Brief

## Report Type
（**必填**：方向汇报型 / 立项材料型 / 决策备忘型 / 学习调研型 — 见 SKILL.md "报告类型识别"）

## Topic

## Report Goal

## Audience

## Geography

## Time Scope

## Must-Answer Questions

## Constraints And Boundaries

## Source Preferences

## Style Reference

## Full-Report Requirement
```

这是强制用户确认的 artifact。
写完 `Research Brief` 后，暂停等待用户明确确认，然后再撰写 `Search Plan`。

`## Report Type` 决定后续评审的权重和关卡——评审 agent 必须按 `references/scoring.md` 中"报告类型决定权重"的对应公式打分，不能用错权重。如果用户没明说类型，规划 agent 必须主动追问"这份给谁看？老板汇报、项目立项、还是知识沉淀？"，确认后再继续；用户依然未明说则默认为**方向汇报型**。

`## Source Preferences` 中应说明：是否优先微信公众号、券商公开研究、平台公开数据等，以及是否有需要避开的来源类型。默认跳过所有付费墙来源。

`## Style Reference` 是可选字段，但如果用户未提供，**默认使用以下风格画像**（基于用户工作写作风格提炼）：

### 默认风格画像：Analytical Operator + Systems Narrator

**风格代号**：冷峻的商业操盘手 + 工程化叙事者

**核心特征**：
- **数字驱动**：用比例、范围、倍数表达强弱，不说模糊形容词（30%-50%、3-5天→2-4小时、10-20倍）
- **定义式短句定调**：核心是/本质是/关键前提是/差异不在于…而在于…
- **对比结构高频**：传统 vs 新范式、人 vs 系统，表格 10 秒抓差异点
- **叙事闭环**：问题→方案→机制→案例→量化→落地，不堆 facts
- **术语有门槛控制**：术语 + 定义/解释 + 业务意义的三段式，新术语必须回答"定义/解决什么/如何验收"
- **主动降营销味**：避免空泛口号（"全面赋能""颠覆式变革"），用可验证事实和可量化收益说服
- **资源诉求显式**：结论里用"成本端-替代端-收益端"ROI 拆解完成决策闭环

**评审 Agent 在 Style Fit 维度的检查要点**：
- 报告是否有定义式短句定调，而非冗长铺垫
- 数据呈现是否量化、可验证，而非模糊形容
- 是否善用对比表/对照句说清差异，而非平铺罗列
- 结论是否有可执行的资源诉求与 ROI 逻辑
- 是否避免了空泛口号和未解释的术语堆叠

如果用户提供了自己的 reference text，则以用户提供的文风为首要评判基准，覆盖以上默认画像。

### Artifact 2 — Search Plan

```md
# Search Plan

## Search Facets

## Priority Source Classes

## Query Set

## First-Pass Coverage Targets

## Known Risk Areas
```

这是强制用户确认的 artifact。
写完 `Search Plan` 后，暂停等待用户明确确认，然后再启动第一轮搜索。

在 `## Priority Source Classes` 下，默认使用多种来源类型的组合，而非单一发布方类别。对于行业、市场、竞争、渠道或广告支出类主题，在合理情况下应包含公司财报以及至少两类非公司目标来源，例如咨询或行业协会研究、监管机构或官方平台研究、微信公众号来源，以及券商公开分析。

在 `## First-Pass Coverage Targets` 下，标明在起草前哪些主要章节仍需要非公司分析类来源的支持。

### Artifact 3 — Source Index

```md
# Source Index

## Search Records

## Must-Use Sources

## Section Coverage Map

## Blocked Or Unavailable Sources

## Remaining Open Evidence Needs
```

在 `## Must-Use Sources` 中，每条来源必须包含官方页 URL 和 PDF URL（如有）。公众号来源须包含原文链接。当更广泛的外部分析合理存在时，不要仅依赖公司财报。

在 `## Section Coverage Map` 中，标注哪些章节仍仅由发行方披露支撑，以及在起草前是否需要另一轮搜索。

搜索记录保存在 `report_runs/<slug>/search-records/` 下，格式参见 `search-record-format.md`。

### Artifact 4 — Storyline Packet

```md
# Storyline Packet

## Title

## Thesis
[一句话核心命题：这份报告要回答什么问题？为什么这个问题重要？]

## Narrative Arc
[故事线：从现象到模式到决策的逻辑链条。不是按公司罗列，而是按张力/趋势/矛盾组织]

## Structural Tensions / Patterns (3-5 个)
[每个 tension/pattern 包含：]
### Pattern 1: [名称]
- **Phenomenon**: [跨多个研究对象的可观察事实，用对比或案例呈现]
- **Underlying Logic**: [不是技术解释，而是商业逻辑、市场结构、博弈机制的解释]
- **So What**: [对读者的具体含义——这改变了什么、该怎么做、不做的代价是什么]

### Pattern 2: [名称]
...

## Causal Network
[多个 pattern 之间的因果关系：哪些是硬约束、哪些是衍生现象、哪些是互为条件]

## Counter-Consensus Insight
[至少 1 个反共识判断：行业共识是什么？有没有证据表明共识可能是错的？]

## Proposed Sections

## Section Evidence Plan

## Open Questions

## Boundaries
```

**关键要求**：
- Storyline Packet 必须以 insights 驱动，不能是"逐个公司描述"的变体
- 每个 Pattern 必须形成"现象→逻辑→So What"完整闭环
- 必须有 Causal Network（pattern 间的因果关系）
- 必须至少 1 个 Counter-Consensus Insight

这是强制用户确认的 artifact。
写完 `Storyline Packet` 后，暂停等待用户明确确认，然后再起草报告。

### Artifact 5 — 报告

```md
# 报告

## Research Question

## Executive Summary

## Report Body

## Current Evidence Limits
```

在 `## Report Body` 内部，依赖来源的段落必须包含可点击的 Markdown 引用，例如 `[来源标题](URL)`。裸名称不通过引用链接关卡。

跨公司、全市场或全渠道的论断，在更广泛的外部来源合理存在时，不应仅依赖发行方自我描述。

报告按版本递增命名：`05-report-v1.md`、`08-report-v2.md`，等等。

### Artifact 6 — 评审

```md
# 评审

## Overall Verdict

## Scores

## Gate Checks

## Reality Check（逍姐视角）

### 商业本质检查
- [建议X] 能赚钱吗？收入从哪来？

### 真问题 vs 假问题
- [焦虑Y] 是真问题还是脑补？证据链是什么？

### 竞对辩证
- [竞对做了Z] 他们的场景变量我们有吗？先行条件是什么？

### 可行性评估
- [建议W] 团队从哪来？预算谁批？停止条件是什么？

### 成功标准
- [方案V] 什么算好？说不清说明没想明白

### MVP 路径
- 最痛的商家是谁？怎么伴随测试？

## Findings

## Missing Or Thin Sections

## Required Next Action

## Follow-Up Search Requests

## Blocked Items
```

在 `## Findings` 中，指出 `Research Brief` 中任何仍缺乏充分支撑的 `Must-Answer Questions`。
不要在未明确标注为需要用户审批的 scope 缩减的情况下，按照一个更窄的非官方论点来进行审批。

`## Required Next Action` 的路由决定为以下之一：`rewrite`、`search`、`rewrite+search`、`blocked`、`pass`。

**Reality Check 是硬性要求**：每个战略建议都必须通过 6 个追问，否则触发逍姐关卡失败，路由到 `rewrite` 或 `search`。

### Artifact 7 — Follow-up Search Brief

```md
# Follow-up Search Brief

## Why Another Search Is Needed

## Priority Gaps

## Target Source Types

## Query Additions

## Expected Report Sections Affected
```

这不是常规用户确认 artifact。
用它来规范额外的搜索轮次，仅当新一轮搜索改变了 scope 或引入了用户协助依赖时才暂停等待用户确认。

补搜轮次同样遵循 HQS 增强搜索规则。

### Artifact 8 — run-status.md

```md
# 运行状态

## 当前阶段

## 已完成

## 阻塞项

## 待整合材料

## 下一步
```

断点恢复的核心文件。当路由为 `blocked` 或会话中断时写入运行目录。新会话读取此文件 + 最新评审文件继续工作。

### Artifact 9 — Final Report

```md
# Final Report

## Executive Summary

## Report Body

## What This Report Can Reliably Support

## What Still Needs Human Input
```

在 `## Report Body` 内部，依赖来源的段落必须包含可点击的 Markdown 引用，例如 `[来源标题](URL)`。裸名称不通过引用链接关卡。

跨公司、全市场或全渠道的论断，在更广泛的外部来源合理存在时，不应仅依赖发行方自我描述。

### Artifact 10 — Evidence Gap Log

```md
# Evidence Gap Log

## Confirmed Evidence

## Assumptions

## Gaps Requiring Search

## Gaps Requiring Human Help
```
