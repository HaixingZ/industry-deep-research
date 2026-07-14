# Review-Rewrite Loop Scripts

deep-industry-research 报告 v1 写完后，用这套脚本管理"评审-修改"循环。

## 设计原则

- **脚本做仪表盘，AI 做判断**：脚本只负责状态管理 + Prompt 渲染 + 解析 + 路由决策；评审和修改本身仍由独立 sub-agent 完成
- **沙盒可执行 sub-agent 调用**：脚本不直接 spawn sub-agent（Python 没法调 OpenClaw 的 sessions_spawn），由主会话 agent 拿到 prompt 后用工具发起
- **状态持久化**：所有信息写在 `<run-dir>/review-state.json`，跨会话也能续跑
- **机器可解析的 sub-agent 输出**：review/rewrite sub-agent 必须在结尾输出 `<<<REVIEW_RESULT>>>...<<<END>>>` 或 `<<<REWRITE_RESULT>>>...<<<END>>>` JSON 块

## 文件清单

- `review_loop.py` — 主 CLI（init / prepare-review / parse-review / prepare-rewrite / mark-rewrite / status / decide）
- `lint_report.py` — 规则 lint，跑在 sub-agent 评审之前，先把硬规矩违规清掉
- `templates/review_prompt.md` — review sub-agent 任务模板
- `templates/rewrite_prompt.md` — rewrite sub-agent 任务模板

## 典型用法（主会话 agent 视角）

```bash
# 报告 v1 已写完，初始化循环
uv run review_loop.py init \
  --run-dir report_runs/wechat-ai/ \
  --type knowledge_build \
  --title "微信 AI 调研：能力扫描"

# 预先跑规则 lint，先把推销词/裸链/storyline 标题等硬伤清掉
uv run lint_report.py report_runs/wechat-ai/final-report.md \
  --brief report_runs/wechat-ai/research-brief.md
# 退出码非 0 = 有 P0/P1 违规，建议先修

# 拿 review prompt（可加 --output-json 让主 agent 直接读 task 字段）
uv run review_loop.py prepare-review --run-dir report_runs/wechat-ai/
# 主 agent 把输出复制到 sessions_spawn(agentId="main", task=<output>)

# Sub-agent 完成后，把结果落到 review-round-N.md，然后：
uv run review_loop.py parse-review --run-dir report_runs/wechat-ai/
# 输出 JSON: {round, score, route, decision: continue|pass|plateau|...}

# 如果 decision == continue，拿 rewrite prompt
uv run review_loop.py prepare-rewrite --run-dir report_runs/wechat-ai/
# 主 agent spawn rewrite sub-agent

# Rewrite sub-agent 完成后
uv run review_loop.py mark-rewrite --run-dir report_runs/wechat-ai/
# 自动从 rewrite-round-N.log.md 解析 items_addressed/items_skipped

# 回到 prepare-review，循环
```

## 停止条件

`decide` 命令返回的语义：

- `pass`：score ≥ 9.0 或 sub-agent 显式返回 route=pass
- `plateau`：连续 2 轮 Δ < 0.7 分（或 sub-agent 显式返回 plateau=true）
- `max_rounds`：默认 5 轮兜底
- `blocked`：sub-agent 返回 route=blocked
- `continue`：继续下一轮

## 中途接入既有评审

第一次跑这套脚本时，如果之前已经手动跑了若干轮 review（比如 `review-round-1.md` 和 `review-round-2.md`），可以用：

```bash
uv run review_loop.py init \
  --run-dir report_runs/wechat-ai/ \
  --type knowledge_build \
  --title "..." \
  --starting-round 2
# → 自动从 review-round-1.md 和 review-round-2.md 的 <<<REVIEW_RESULT>>> 块 hydrate 历史
```

## 现有报告兼容

第一版的两份评审报告（review-round-1.md / review-round-2.md）是手写的，没有 `<<<REVIEW_RESULT>>>` JSON 块。要让 `--starting-round` 工作，需要在两份报告末尾手动追加 JSON 块（一次性迁移成本）。新跑的循环不需要这一步。

## 与 SKILL.md 工作流的关系

SKILL.md "工作流概览"第 7 步"评审-修改循环"由这套脚本承载。前 6 步（Brief / Search Plan / Source Index / Storyline / v1）仍走 SOP + 人工确认，不动。
