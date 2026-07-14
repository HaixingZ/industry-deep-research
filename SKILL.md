---
name: deep-industry-research
description: Use when the user needs a full research report, industry study, or company analysis. Defaults to Chinese-language reports with China-market focus. Covers public sources including WeChat official accounts; skips paywalled sources.
allowed-tools: [Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Bash, Agent, TaskCreate, TaskUpdate, AskUserQuestion]
---

# 深度行业研究

## 概述

双 agent 研究报告系统。将高质量搜索方法论嵌入报告写作全流程。

- **规划/评审 Agent**（通过 Agent tool 启动为独立子 agent）：制定计划、设定标准、评审报告、打分、路由决定
- **执行 Agent**（主会话 agent）：搜索资料、写报告、根据评审反馈修改
- **通信方式**：通过 artifact 文件（写入 `report_runs/<slug>/`），不通过对话历史
- **搜索方式**：HQS 增强搜索（来源优先级阶梯、公众号搜索、双语检索、PDF 优先）
- 自动迭代直到质量无法再提升或信息获取受阻
- 默认产出中文报告，搜索以中文为主，聚焦中国市场
- 跳过所有付费墙/登录墙来源

## 执行前门控（防跳步，必读必做）

**这是硬规矩，违反直接算流程失败，不给自己找借口。**

### 每次进入 skill 的第一个动作

1. 读 `report_runs/<slug>/run-state.json`（不存在就用 `review_loop.py init` 初始化）——**在读 state 之前不许做任何其他动作**
2. 读 `report_runs/<slug>/run-progress.md`（不存在就创建），确认当前在哪一步
3. 在回复开头 print 一段"执行仪表盘"：
   ```
   📍 阶段：<阶段一信息确认 / 阶段二报告生成 / 阶段三评审循环>
   📍 当前步骤：<第 N 步，具体名称>
   📍 已完成确认点：Brief✓ / Search Plan✓ / Source Index✗ / Storyline✗
   📍 Review round: <N/最少2轮>  score: <x.x>  Δ: <x.x>  plateau: <0/2>
   ```
4. 每完成一步：追加一行到 `run-progress.md`，并调用 `review_loop.py mark-*` 更新 state
5. 在用户确认节点，**输出完 artifact + 仪表盘就停**，不许在同一回复里推进下一步（即使用户前面说过"继续"也只是走下一步、不是跳步）

### 评审循环硬约束

- **必须用 sub-agent 跑评审**，主会话直接给报告打分算违规。调用范式：
  ```
  sessions_spawn(
    runtime="subagent",
    mode="run",
    task=<review_loop.py prepare-review 输出的 prompt>
  )
  ```
- **最少跑 2 轮 review**（例外：首轮 ≥ 9.5 且 7 关卡全通过才能一轮结束）
- **禁止在 `state.phase != "final"` 时写 `final-report.md`**——lint_report.py 会拦
- 每轮 review 结束后必须调用 `review_loop.py parse-review` 拿 route，再决定下一步。不许"看了看觉得差不多"就交付

### 违规信号（出现任何一个立即停下自查）

- 没读 run-state.json 就开始写作或搜索
- 主会话里直接对报告打分/评审（应该 sessions_spawn 出去）
- v1 写完直接输出 final-report.md（跳过评审循环）
- 只跑了 1 轮 review 就交付（首轮分数不到 9.5）
- 回复里没有"执行仪表盘"那 4 行
- context 长了想"简化收敛"——这就是典型的跳步动机，停下来读 SKILL.md 对应章节

---

## 适用场景

适合：
- 完整研究报告（行业、市场、公司）
- 需要多轮搜索才能补齐内容的长文档
- 中国市场深度研究（公众号为主要信源之一）
- 部分所需材料在公开渠道可能稀缺的研究任务

不适合：
- 只需要 source packet 而不需要综合分析
- 需要明确选项排名的决策 memo
- 以执行排期为核心的执行方案

## 报告类型识别（Step 0：写 Brief 之前必须确定）

写 Research Brief 之前，规划 agent 必须先和用户确认报告类型，因为不同类型对评审维度的取舍完全不同。

| 类型 | 谁看 | 用途 | Reality Check 适用性 | 推荐骨架 |
| --- | --- | --- | --- | --- |
| **方向汇报型**（Direction Memo） | 老板 / 决策层 | 答"该走哪条路"——竞品在做什么、行业方向是什么、我们怎么对标 | ⚠️ **不适用** | `references/templates.md` → 调研报告骨架 |
| **立项材料型**（Project Proposal） | 项目组 / 跨团队对齐 | 答"我们要怎么做"——MVP 路径、成功标准、Kill Criteria、投入估算 | ✅ 完全适用 | `references/templates.md` → 方案/提案骨架 |
| **学习/调研型**（Knowledge Build） | 自己 / 团队内部沉淀 | 答"这是什么、它怎么工作"——竞品技术栈、架构原理、行业术语 | ⚠️ 部分适用 | `references/templates.md` → 调研报告骨架（去掉快手对照段） |
| **决策备忘型**（Decision Memo） | 决策层 / 跨级汇报 | 答"在 A/B/C 之间选哪个"——选项排名 + 决策矩阵 + 推荐 | ✅ 适用 | `references/templates.md` → 方案/提案骨架 |
| **业务复盘型**（Review） | 团队内部 | 答"做对了什么 / 做错了什么"——归因 + 经验 + 下一阶段动作 | ✅ 适用 | `references/templates.md` → 业务复盘骨架 |
| **访谈纪要型**（Interview Summary） | 团队内部 | 答"各位被访者说了什么"——共识 + 分歧 + 待验证假设 | ⚠️ 部分适用 | `references/templates.md` → 访谈纪要骨架 |

**判断规则**：

- 用户没明说类型 → 主动追问（"这份给谁看？老板汇报还是项目立项？"）
- 默认 → **方向汇报型**（最常见）
- 类型一旦确定，写在 Research Brief 头部，评审 agent 必须按对应类型的标准评分

## 写作硬规矩（适用于所有类型）

以下规则分两层：**快手汇报规矩**（来自 USER.md，最高优先级）和**行文规矩**（来自 business-writing style-guide，锁死风格不漂移）。

### 快手汇报规矩（最高优先级）

- **没和相关方对齐过的具体动作和具体数字，不进汇报**——MVP 路径、Kill Criteria、阈值（命中率 X%、误操作 < Y 元）、时间表（P0/P1/P2 + 投入工程师月）这类内容，没有跨团队对齐过都属于"拍脑袋"。一旦写进汇报，老板第一句就会追问数字怎么来的，答不上来就掉信任
- **拍脑袋的内容宁可不写，也不要"待补"占位**——"待补"在汇报里读起来像没做完功课
- **冷静描述 > 推销性形容词**：删除"最完整""极高""值得直接对标"等评价性表述，老板看到"最 X"会本能怀疑
- **每节末尾的"对快手的启示 / 对我们意味什么"段落会干扰阅读**：洞察融进正文，不另起段落
- **storyline 句式适合 PPT 标题，不适合长文标题**：长文用简洁的"X 是什么 / X 长什么样"式短标题；PPT/单页 onepage 才用一句话立论式标题
- **竞品分析必须落到自家具体项目**：横向扫描后必须有"我们怎么对标 / 我们的项目长什么样"的收口章节，不能只给"参考蓝图"
- **内部组织信息是核心资产**：能拿到的内部分工 / MCP 调用关系 / 团队归属信息，往往能产生比公开资料更好的 insight，必须主动追问用户能否提供

### 行文规矩（风格锁死，详见 references/style-guide.md）

- **章节用数字编号（一、二、三），小标题用问句** — ✅ "集采发生了什么"；❌ "供给侧增量分析"
- **小标题数量控制在全文 15 个以内** — 超过则合并或降级为加粗引导句
- **每个大板块讲完竞对做法后，紧跟"快手对照"** — 不是集中在最后一节，是每节讲完就给判断
- **待办按依赖关系排序** — "本周内（无技术依赖）" / "2-4 周内（需内部协同）" / "季度内（需专项资源）"
- **口径存疑集中在一节** — 标题"待办与口径"，不散落
- **bullet point 优先** — 2-3 层缩进，加粗 lead → 子项展开，不写大段散文
- **表格只在并列对照场景使用** — 品类占比、平台对比、客户分层等；其他场景用 bullet
- **数据嵌入句子里** — ✅ "25 年市占 31%，YoY 份额 -1pp"；❌ 数字另起一行
- **不发明原文外的概念** — ❌ "五维资源重构体系"（模型自造框架词）
- **不外推未披露的数据** — 专家说了 +3pp 但没说下游影响 → 不推算
- **引用专家原话时直接给原话** — "专家原话："前缀，引号内保留原文措辞
- **推断必须显式标注** — "50% > 30% + 15%：老客户深挖比新客拓展增量更大"（算术，非推测）
- **句子短、判断硬** — 陈述句，不用引导性话术
- **不用 emoji 和花哨符号**

### 防幻觉检查清单（写完报告后逐条自查）

- [ ] 全文是否有任何"框架名"是模型自己发明的？
- [ ] 是否有任何数据点在原文里找不到对应句子？
- [ ] 是否有任何过渡句凭空出现？
- [ ] "快手对照"段落里是否有原文素材无法支撑的建议？
- [ ] 是否外推了专家未披露的下游影响？
- [ ] 是否把推测写成了结论？
- [ ] 小标题是否有非问句的概括性标题？
- [ ] 是否有 emoji 出现在正式正文中？
- [ ] 是否有没对齐过的具体动作/数字被写进了汇报？

---

## 工作流概览

1. 规划/评审 agent 写 Research Brief → 等用户确认
2. 规划/评审 agent 写 Search Plan → 等用户确认
3. 执行 agent 按 HQS 增强搜索规则搜索 + 建 Source Index + 存档搜索记录
4. 执行 agent 写 Source Index 摘要 → **等用户确认**（信息是否充分、有没有遗漏方向）
5. 执行 agent 写 Storyline Packet（含逍姐预审） → 等用户确认
6. 执行 agent 全力写报告 v1 → **此后全自动**
7. 评审-修改循环：规划/评审 agent 评审打分路由 → 执行 agent 根据反馈行动 → 循环（**用 `scripts/review_loop.py` 管理状态和 prompt 渲染，详见 `scripts/README.md`；rewrite 完成后跑 `scripts/lint_report.py` 先把规则能命中的硬伤清掉再交给 review**）
8. 平台期检测：连续 2 轮提升 < 0.7 分且剩余弱点主要被信息获取阻塞 → 停止并交付

详见 `references/workflow.md`

## 搜索操作规则（HQS 增强版）

搜索能力内置于执行 agent，6 步流程：

1. **分解搜索面** — 把报告需求拆成主题、地域（默认中国）、时间范围（默认 3 年）、来源类型（含微信公众号）、文档类型
2. **按优先级搜索** — 读取 `references/source-priority.md`、`references/china-source-map.md`、`references/query-patterns.md`、`references/broker-research-playbook.md`。先搜官方域名和 PDF，穷尽后再扩大范围。跳过付费墙来源。微信公众号为必搜渠道（通过搜狗微信搜索或 mp.weixin.qq.com）。
3. **飞书对外文档搜索站**（竞对相关时必做） — 读取 `references/feishu-search-integration.md`，用 agent-browser 访问 https://feishusearch.frontend-cloud.corp.kuaishou.com 搜索字节对外文档。标题可直接引用，标注来源"字节对外文档《XXX》"。需 SSO 登录时用 kuaishou-sso-login-client skill。
4. **验证文档** — 确认标题、出版方/公众号名称、日期、原创性；优先出版方自己的 PDF URL；明确标注访问标签
5. **排序去重** — 按权威性、相关性、时效性、原创性排序；去掉薄弱摘要和 SEO 页面
6. **交付 Source Index** — 每条来源必须包含官方页 URL 和 PDF URL（如有）。公众号来源需包含原文链接。飞书搜索站来源需标注"字节对外文档"。
7. **存档搜索记录** — 写入 `report_runs/<slug>/search-records/`，格式见 `references/search-record-format.md`，每条来源强制记录内容摘要块

每轮额外搜索（包括 Follow-up Search）必须同样遵循此 6 步流程。

## 报告写作规则

- 每一版报告都必须全力写作，不存在"先交个及格版再说"
- **可点击 citation 是硬性要求**：所有依赖来源的段落必须在相关段落末尾添加可点击 Markdown 链接，格式为 `[来源标题](URL)`
- 不允许只写来源名称不加链接
- 跨公司、市场级、渠道级的论断不能仅依赖公司自述，需要非公司分析来源支撑
- 评审 agent 的关卡检查中包含"引用链接关卡"：未加链接即不通过

### Insight 驱动：从 Facts 到 Patterns 到 So What

**核心原则：报告不是 facts 的堆砌，而是 insights 的提炼。** 读者（尤其战略分析师）需要的不是"14 个平台分别做了什么"，而是"这些差异背后是否有结构性规律"。

**报告结构必须以 insights 驱动，而非按研究对象逐个描述**：
- **禁止**：按公司/平台/产品逐个罗列的"百科全书式"结构
- **要求**：以核心命题（thesis）开头，用结构性张力（tensions）或模式（patterns）组织正文，公司细节放附录

**每个 pattern 必须形成完整闭环**：
1. **现象**（What）：跨多个平台的可观察事实，用对比表或案例呈现
2. **底层逻辑**（Why）：不是技术解释，而是商业逻辑、市场结构、博弈机制的解释
3. **So What**（意味着什么）：对读者的具体含义——不是泛泛的"值得关注"，而是"这改变了什么、该怎么做、不做的代价是什么"

**提炼模式的思维工具**：
- **张力识别**：找到看似矛盾的现象（如"自动化越高，透明度越低"），追问为什么
- **因果网络**：多个张力不是并列的，它们之间有因果关系（如"信任缺口是硬约束，其他张力在天花板下展开"）
- **反共识判断**：行业共识是什么？有没有证据表明共识可能是错的？
- **历史类比**：当前现象是否在历史上发生过类似模式（如"决策层被第三方捕获→平台沦为管道"的历史先例）
- **原创概念**：如果有必要，给反复出现的模式命名（如"问责链长度""生态拓扑"）

**Storyline Packet 阶段必须产出**：
- 核心命题（一句话概括报告的核心论点）
- 3-5 个结构性张力或模式（每个都包含现象→逻辑→So What 的雏形）
- 模式间的因果关系图（哪些是硬约束、哪些是衍生现象）
- 至少一个反共识判断

**评审 agent 在 Insight 维度的检查项**：
- 报告是否有清晰的 thesis（核心命题）而非"全面覆盖"
- 每个 pattern 是否形成"现象→逻辑→So What"的完整闭环
- 是否提炼出跨平台的结构性规律，而非停留在单个平台的描述
- 是否有原创的分析概念或框架（不是生搬硬套已有理论）
- So What 是否具体（"应该做什么"而非"值得关注"）
- 附录中的事实细节是否服务于正文中的论点（不是为完整而完整）

### 文风复刻

Style Reference 默认使用用户的 Analytical Operator 风格画像（数字驱动、定义式短句定调、对比结构、叙事闭环、降营销味），详细定义见 `references/output-contracts.md` 的 Style Reference 章节。

如果用户在 Research Brief 的 `## Style Reference` 中提供了自己历史写作的样本文本，评审 Agent 在 Style Fit 维度中必须将样本文风作为首要评判基准，覆盖默认画像。检查维度包括：
- **句式节奏**：长句/短句比例、段落长度、是否善用短段推进
- **用词偏好**：术语选择、是否使用英文穿插、书面化程度
- **段落组织**：结论前置/演绎推后、是否用标题分层、过渡方式
- **数据呈现**：数据放在段落中还是独立表格、是否习惯用数据开头
- **语气与姿态**：断言的自信程度、是否使用第一人称、是否有价值观表达

Style Fit 评分逻辑：如果提供了 reference text 但报告风格偏离明显 → 路由到 `improve`，要求执行 Agent 对照原始文风重新润色。未提供 reference text 时，按默认风格画像评判。

## 评审规则

规划/评审 agent **必须**通过 `sessions_spawn(runtime="subagent", mode="run", task=...)` 作为独立子 agent 启动，主会话就地评审算违规（会导致自评偏差和 context 溢出跳步）。

调用范式：
```
# 1. 生成 prompt
uv run scripts/review_loop.py prepare-review --run-dir report_runs/<slug>/
# 2. 把输出的 task 字段丢进 sub-agent
sessions_spawn(runtime="subagent", mode="run", task=<prompt>)
# 3. sub-agent 完成后把结果写到 review-round-N.md，再解析
uv run scripts/review_loop.py parse-review --run-dir report_runs/<slug>/
```

- 评审时读取：最新 Research Brief + 最新报告 + Source Index + 搜索记录
- 打分维度见 `references/scoring.md`（Coverage / Logic / Insight / Expression / Style Fit / **Reality Check**）
- 7 个关卡检查：完整报告关卡、证据卫生关卡、引用链接关卡、Brief 对齐关卡、深度研究来源组合关卡、来源充分性关卡、**逍姐关卡（Reality Check Gate）**
- **Reality Check（逍姐视角）占 20% 权重**，6 个追问：能赚钱吗？是真问题吗？竞对做了≠我们也要做？能不能干成？成功标准是什么？MVP 路径在哪？
- 通过阈值 **9.0/10**，不通过则 `rewrite`（重写）或 `search`（补搜），不是温和的 improve
- 评审者必须具体、怀疑、行动导向，不泛泛表扬
- 核心优势：评审者就是制定标准的人，不存在理解偏差
- 详见 `references/partner-review.md`

## 路由逻辑

评审后路由为以下之一：

- `rewrite` — 不缺信息但写法有问题，重写对应章节（不是温和的 improve）
- `search` — 缺信息，补搜公开信息（含微信公众号），自动继续
- `rewrite+search` — 既缺信息又写得不好，先搜再重写
- `blocked` — 信息无法通过公开渠道获取，暂停，写 run-status.md 记录断点
- `pass` — 总分 >= 9.0 且所有关卡通过，产出 final-report.md 和 evidence-gap-log.md

## 断点恢复

当路由为 `blocked` 或会话中断时：

- 自动写 `run-status.md` 到运行目录，记录当前阶段、已完成项、阻塞项、待整合材料、下一步
- 用户在新会话中提供新材料后，skill 读取 `run-status.md` + 最新评审文件，按完整标准继续迭代
- 恢复后仍然使用 skill 的全套质量标准，不退化为无 skill 的普通写作
- 详见 `references/artifact-storage.md`

## 危险信号

出现以下情况时立即停下检查：

- 你在搜索之前就在写正文
- 你把 source packet 或大纲当作完整报告
- 你准备在没有独立评审的情况下批准草稿
- 内容薄弱因为证据缺失，但你只在改写文字
- 来源主要是年报和公司自述，而更广泛的外部研究很可能存在
- 起草者或评审者在悄悄重新定义论题以适应可用来源
- 你跳过了 Research Brief、Search Plan 或 Storyline Packet 的用户确认
- 需要的来源被阻塞但你没有写 run-status.md 记录
- 你在没有先写 Follow-up Search Brief 的情况下启动新一轮搜索
- 依赖来源的段落提到了报告名称但没有可点击链接
- 没有搜索微信公众号就认为中文来源已穷尽
- 你纳入了需要付费或登录才能访问的来源
- 你准备把关键工作状态遗漏在 artifact 链之外

## 常见错误

- 在做正式来源搜索之前就开始起草
- 跳过 3 个必需用户确认节点
- 停在公司年报而从未检查咨询、券商、协会、监管、平台、微信公众号或测量研究
- 让报告悄悄从已批准的 brief 漂移到更小的论题
- 让执行 agent 自己评审自己的报告
- 只写报告名称而不添加可点击 Markdown 引用
- 用户要求完整报告时产出了缩短的 memo
- 真正的阻塞是缺少材料时继续改写
- 未保存中间 artifact，导致长流程工作难以恢复
- 搜索时不验证文档真实性，返回无效链接
- 评审时用更窄的"当前论题"替代已批准的 brief 来放行
- 没有搜索微信公众号就认为中文搜索已完成
- 纳入了付费墙来源

## 引用文档

按需读取：

- `references/workflow.md` — 固定流程、路由规则、停止规则、断点恢复协议
- `references/artifact-storage.md` — artifact 保存位置、命名规则、run-status.md 规范
- `references/output-contracts.md` — 搜索来源包格式 + 所有 artifact 精确格式
- `references/scoring.md` — 评分维度、关卡、通过阈值
- `references/partner-review.md` — 规划/评审 agent 职责说明
- `references/deep-research.md` — 行业级研究的来源组合预期
- `references/evidence-gap.md` — 证据/假设/缺口/被阻塞来源处理
- `references/harness-principles.md` — 双 agent 架构原则
- `references/source-priority.md` — 来源优先级阶梯（含微信公众号）
- `references/china-source-map.md` — 中国市场来源地图（含微信公众号）
- `references/query-patterns.md` — 搜索查询模式（含微信公众号搜索）
- `references/broker-research-playbook.md` — 券商公开研究获取策略
- `references/search-record-format.md` — 搜索档案存档格式（含来源内容摘要）
- `references/templates.md` — 四种文档类型骨架模板（调研报告/访谈纪要/业务复盘/方案提案）
- `references/style-guide.md` — 行文规则 + 快手硬规矩 + 防幻觉检查清单
- `references/feishu-search-integration.md` — 飞书对外文档搜索站接入规则
