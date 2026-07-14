# 搜索查询模式

使用窄到宽的搜索循环。从可能的出版方开始。仅在官方路径穷尽后扩大范围。

## 核心操作符

- `site:domain.tld` — 限定域名
- `filetype:pdf` — 限定 PDF 文件
- 引号精确匹配标题或主题词
- 年份过滤如 `2024`、`2025` 或具体月份
- 中文和英文主题、出版方和文档类型的变体（中文优先，英文补充）

## 搜索循环

### 1. 官方域名 PDF 搜索

当已知可能的出版方时使用。

示例：
- `"半导体" filetype:pdf site:mckinsey.com`
- `"电动车" filetype:pdf site:bcg.com`
- `"人工智能" "白皮书" filetype:pdf site:miit.gov.cn`

### 2. 官方落地页搜索

当 PDF 未被直接索引时使用。

示例：
- `"半导体报告" site:mckinsey.com`
- `"生成式 AI" "白皮书" site:出版方域名`
- `"2025 展望" site:机构域名`

### 3. 标题导向搜索

当从发现阶段已知可能的文档标题时使用。

示例：
- `"AI 行业研究报告" pdf`
- `"中国汽车行业白皮书" pdf`
- `"新能源汽车市场展望" filetype:pdf`

### 4. 微信公众号搜索

优先搜索渠道：搜狗微信搜索 (weixin.sogou.com)。
补充：`site:mp.weixin.qq.com 关键词`

搜索模式：
- 机构名 + 关键词：`"中金" "行业深度" site:mp.weixin.qq.com`
- 主题 + 公众号：`"新能源" "研报" site:mp.weixin.qq.com`
- 报告标题搜索：`"中国XX行业展望" site:mp.weixin.qq.com`
- 全公众号搜索：`"白皮书" "2025" site:mp.weixin.qq.com`

标注来源类型为 `wechat official account`。

### 5. 券商公开研究搜索

搜索官方机构名称加上文档意图。

公开研究搜索模式：
- `"机构名" 行业深度 pdf`
- `"机构名" 策略报告 pdf`
- `"机构名" 研究所 行业 观点`
- `"券商名" 年度策略 pdf`

注意：仅纳入公开可访问的研究。付费墙后的研究直接跳过。

### 6. 白皮书搜索

使用出版方加文档类别。

示例：
- `"主题" "白皮书" pdf "机构名"`
- `"主题" white paper pdf 协会`
- `"行业" 白皮书 filetype:pdf`

### 7. 监管机构和交易所搜索

使用主题加文档类别和管辖范围。

示例：
- `"数据要素" 指南 pdf 监管`
- `"做空" 报告 pdf 证监会`
- `site:szse.cn "规则" filetype:pdf`
- `site:csrc.gov.cn "征求意见稿"`

### 8. 中文互联网平台公开数据搜索

示例：
- `site:oceanengine.com 行业报告`
- `"巨量算数" 报告 filetype:pdf`
- `"QuestMobile" "报告" filetype:pdf`

## 中英双语扩展

中文为主，英文补充。当主题在中国和英语生态中都有重要来源时：

1. 先搜中文主题 + 中文文档类型
2. 再搜英文主题 + 英文文档类型（仅当中文来源不足时）
3. 混合形式：当机构名是英文但市场是中国时

中文文档类型：
- `报告`
- `白皮书`
- `洞察`
- `展望`
- `研报`
- `路演材料`
- `投资者演示`
- `行业深度`
- `年度策略`
- `统计公报`

英文文档类型（补充使用）：
- `report`
- `white paper`
- `outlook`
- `primer`
- `deck`
- `annual report`
- `investor presentation`

## 搜索失败恢复

如果直接 PDF 搜索失败：
1. 搜索官方落地页
2. 不带 `site:` 搜索可能的标题
3. 搜索主题 + 出版方 + 年份
4. 在相邻官方域名上搜索主题 + 文档类别
5. 仅在此后检查高质量的二次引用以获得原始标题和出版方线索

## 每条保留来源的必填信息

- 标题
- 出版方/公众号名称
- 日期
- 来源类型
- 访问标签（`official PDF` / `official page` / `wechat official account` / `authorized distribution` / `secondary mirror`）
- 官方页面 URL
- 直接 PDF URL（如有）
- 一句话说明为什么重要

---

## 相关文档

- [source-priority.md](source-priority.md) — 来源优先级阶梯（定义访问标签）
- [china-source-map.md](china-source-map.md) — 中国市场来源地图
- [broker-research-playbook.md](broker-research-playbook.md) — 券商研究获取策略
