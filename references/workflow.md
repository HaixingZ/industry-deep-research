# 工作流程

## 固定流程

### 阶段一：信息确认（需用户确认）

1. 创建运行目录 `report_runs/<slug>/` 并初始化 artifact 链
2. 规划/评审 agent 写 `Research Brief`
3. **等用户确认** `Research Brief`
4. 规划/评审 agent 写 `Search Plan`
5. **等用户确认** `Search Plan`
6. 执行 agent 按 HQS 增强搜索规则搜索第 1 轮
7. 执行 agent 写 `Source Index`（包含公众号来源）
8. 执行 agent 存档搜索记录至 `search-records/`
9. **等用户确认** `Source Index`（用户检查信息是否充分、有无遗漏方向）
10. 执行 agent 写 `Storyline Packet`（含逍姐预审）
11. **等用户确认** `Storyline Packet`

### 阶段二：报告生成（全自动，无需用户干预）

12. 执行 agent 读取 `references/templates.md`，按 Step 0 确定的报告类型选择对应骨架
13. 执行 agent 读取 `references/style-guide.md`，严格遵循行文规则
14. 执行 agent 全力写报告 v1（按骨架 + 风格规则 + 防幻觉检查清单）
15. 规划/评审 agent 评审报告（6 维度 + 7 关卡）
16. 根据路由决定下一步（`rewrite` / `search` / `rewrite+search`）
17. 执行 agent 根据评审反馈重写或补搜
18. 重复 15-17 直到满足停止条件
19. 产出 `final-report.md` 和 `evidence-gap-log.md`

**阶段二全自动原则**：
- 评审 → 重写 → 再评审 循环无需用户确认
- 如果评审路由到 `search`（补搜信息），执行 agent 直接补搜后继续，不询问用户
- 只有当评审路由到 `blocked`（信息无法公开获取）时才暂停并通知用户
- 持续迭代直到 `pass`（≥9.0 分且所有关卡通过）或平台期（连续 2 轮提升 < 0.7 分）

## 里程碑用户确认规则

工作流程有 4 个必需确认点（全部在阶段一）：
- `Research Brief`
- `Search Plan`
- `Source Index`（新增：确认信息充分性）
- `Storyline Packet`

在用户明确批准或要求修改之前，不得越过每个确认点继续推进。

以下环节不需要用户确认（阶段二全自动）：
- `Follow-up Search Brief`
- 额外搜索轮次
- 评审后的重写轮次
- 评审路由到 `search` 时的补搜

例外：如果后续轮次提议缩窄 scope、重大论点变更或新增对用户持有材料的依赖，则停下来请用户审批该变更后再继续。

## HQS 增强搜索规则（第 1 轮及所有后续搜索轮次）

每轮搜索必须按以下 7 步执行：

1. **分解搜索面** — 把搜索需求拆成主题、地域（默认中国）、时间范围（默认 3 年内）、来源类型、文档类型
2. **按优先级搜索** — 读取 `source-priority.md`、`china-source-map.md`、`query-patterns.md`、`broker-research-playbook.md`。先搜官方域名和 PDF，穷尽后再扩大范围。跳过付费墙来源。微信公众号为必搜渠道。
3. **飞书对外文档搜索站**（竞对相关时必做） — 读取 `feishu-search-integration.md`，用 agent-browser 访问搜索站搜索字节对外文档。需 SSO 登录时用 kuaishou-sso-login-client skill。
4. **验证文档** — 确认标题、出版方、日期、原创性；优先出版方自己的 PDF URL；明确标注访问标签
5. **排序去重** — 按权威性、相关性、时效性、原创性排序；去掉薄弱摘要和 SEO 页面
6. **交付 Source Index** — 每条来源必须包含官方页 URL 和 PDF URL（如有）。公众号来源需包含原文链接。飞书搜索站来源标注"字节对外文档"。
7. **存档搜索记录** — 写入 `report_runs/<slug>/search-records/`，格式见 `search-record-format.md`，每条来源强制记录内容摘要块

## 评审可用性规则

评审必须由独立子 agent 执行（通过 Agent tool 启动）。
如果无法启动独立 agent，停止工作流程并报告完成被阻塞于独立评审可用性。
不要用自我评审替代。

## 路由逻辑

评审完成后，规划/评审 agent 给出以下 5 种路由之一：

- `improve`
  来源基础已足够，主要提升空间在结构、逻辑、洞察、表达或风格。执行 agent 据此修改报告。

- `search`
  Brief 对齐关卡、来源充分性关卡或深度研究来源组合关卡未通过，且公开来源可能存在。执行 agent 先写 `Follow-up Search Brief`，再执行补充搜索（同样遵循 HQS 增强搜索规则）。

- `improve+search`
  同时需要优化写作和补充搜索。执行 agent 先完成搜索，再基于新来源修改报告。

- `blocked`
  上述关卡未通过，主要因为信息获取受阻（信息不存在于公开渠道、链接失效、需要内部权限等）。输出当前最佳报告、`Evidence Gap Log`，写 `run-status.md` 暂停等待用户协助。

- `pass`
  报告篇幅完整、实质回答了核心问题、通过所有关卡，且剩余局限性已记录。流程结束。

## 平台期检测

当以下条件同时成立时，运行处于平台期：
- 连续 2 轮评审总分提升 < 0.7 分
- 剩余弱点主要被信息获取阻塞（而非写作问题）

当平台期出现时，停止迭代并清晰记录阻塞原因，产出当前最佳报告和 `Evidence Gap Log`。

## 停止规则

**最少必须跑 2 轮 review**（唯一例外：首轮总分 ≥ 9.5 且 7 关卡全通过，可以一轮结束）。

除此之外，当以下条件全部满足时停止：
- 报告实质回答了核心问题
- 报告对齐已批准的 `Research Brief`，而非一个被悄然缩窄的论点
- 独立评审路由为 `pass`，或仅剩 `blocked` 项
- 剩余局限性已记录在 `Evidence Gap Log` 中

**禁止跳步的硬门槛**：
- `state.phase != "final"` 时不许写 `final-report.md`（lint_report.py 会拦）
- Review 必须通过 `sessions_spawn` 独立跑，主会话就地评审算违规
- 每轮循环结束必须调 `review_loop.py parse-review` 拿 route，不许"看着差不多"直接交付

## 断点恢复协议

当路由为 `blocked` 或会话中断时：
1. 写 `run-status.md` 到运行目录，记录当前阶段、已完成项、阻塞项、待整合材料、下一步
2. 新会话读取 `run-status.md` + 最新评审文件继续工作
3. 恢复后使用完整质量标准，不因中断而降低要求

## 搜索循环规则

每轮额外搜索必须从一份书面的 `Follow-up Search Brief` 开始。
不要启动模糊的搜索。首先命名：
- 缺失的章节
- 缺失的证据类型
- 目标来源类别（含微信公众号）
- 预期的报告影响

此 artifact 用于规范搜索路由，不是强制用户确认门控，除非该搜索轮次同时改变了 scope 或需要用户提供材料。

## Brief 对齐规则

已批准的 `Research Brief` 是评审的约束范围。

起草者和评审者必须按照 Brief 的 `Report Goal` 和 `Must-Answer Questions` 来评判报告，而非按照一个悄然缩窄的"当前论点"。

如果草稿仅支持一个比已批准 Brief 更窄的论点：
- 不要路由到 `pass`
- 明确指出 Brief 中哪些问题仍缺乏充分支持
- 如果缺失的支持可能可以获取，路由到 `search`
- 如果缺失的支持被阻塞或无法公开获取，路由到 `blocked`

只有用户可以批准缩窄 scope。agent 可以提议缩窄，但必须将其作为 scope 变更来呈现，而不是表现为原始 Brief 已经被满足。

## 完整报告规则

每一版报告都必须是真正的完整长文。对于深度研究主题，还必须展示真正的来源广度，而不是将一类来源延伸覆盖所有论断。

以下情况不满足此规则：
- 没有展开论述的要点列表
- 伪装成报告的大纲
- 每节只有一两行的章节框架
- 用户要求完整报告时的简短备忘录
