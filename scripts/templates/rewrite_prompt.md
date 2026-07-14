# Rewrite Sub-Agent Task Template

你是 deep-industry-research 工作流里的执行 agent，根据第 {round_n} 轮评审报告修改产出。

## 背景

第 {round_n} 轮评审给出 **{score}/10**，路由 **{route}**。需要按评审清单修改报告，争取在下一轮拉到 9.0+ 或所有关卡通过。

## 你的任务

1. 读取：
   - `{brief_path}` — Brief（必须严格遵守约束）
   - `{report_path}` — 当前版本报告（你要改的对象）
   - `{review_path}` — **第 {round_n} 轮评审报告**（你的工作清单）
   - `{source_index_path}` — 来源索引
   - `{evidence_gap_path}` — 证据缺口

2. 按评审报告"具体修改建议"章节的 P0/P1/P2 优先级**逐项**修改：
   - **P0 必做**：硬关卡相关问题，不修则继续不通过
   - **P1 必做**：USER 硬规矩相关，不修则违反用户红线
   - **P2 视成本做**：提升分数但非硬要求；如果修改需要写未对齐过的数字 / 拍脑袋的判断 / 违反 Brief 排除项，**宁可不做也不要硬凑**

3. **关键边界**（违反则失败）：
   - 不能添加 Brief 排除范围内的内容（横向对标 / 快手对标 / 立项 MVP 等）
   - 不能为了凑分写未对齐过的具体数字 / 拍脑袋的时间表
   - 不能用"待补"占位
   - 不能给推销性形容词

4. **修改时必须用 edit / write 工具直接改 `{report_path}`**，不要新建版本文件

5. **如果某条评审建议你判断不该执行**（比如要求加未验证数字），写到运行日志 `{rewrite_log_path}` 里说明原因，不要静默跳过

6. **完成后必须在最末尾输出一行机器可解析的 JSON**：

```
<<<REWRITE_RESULT>>>
{{"round": {round_n}, "items_addressed": <int>, "items_skipped": <int>, "items_skipped_reasons": ["..."], "summary": "<30 字内总结>"}}
<<<END_REWRITE_RESULT>>>
```

## 修改硬要求

- 改 = 直接动文件，不要做一份"建议清单"返回主 agent
- 改完所有 P0+P1，再做 P2，按优先级顺序
- 每改一条对应一条评审建议，不要漏不要加
- 改写过程中再次扫描全文，避免引入新违规（推销词、storyline 标题、裸链）
