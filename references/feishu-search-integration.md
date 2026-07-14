# 飞书对外文档搜索站接入

> 写报告时，除了搜快手 Docs 和 llm-wiki，还要搜飞书对外文档搜索站，获取字节/小红书/腾讯等竞对的官方文档内容。

## 两个搜索站

- **飞书搜索站**：https://feishusearch.frontend-cloud.corp.kuaishou.com
  - 1303 篇字节对外文档可搜索（标题+关键词）
  - 新增的 1082 篇只有标题没有正文内容，搜索时只能匹配标题关键词
- **知识库站**：https://bytedanceleadkb.frontend-cloud.corp.kuaishou.com
  - 同步更新，同样的数据

## 搜索方式

两个站都需要 SSO 登录。使用 agent-browser 访问：

```bash
# 1. 打开搜索站（会跳转 SSO 登录）
agent-browser open "https://feishusearch.frontend-cloud.corp.kuaishou.com"

# 2. 如果需要登录，用 kuaishou-sso-login-client skill 完成 SSO 认证

# 3. 登录后，在搜索框中输入关键词
agent-browser snapshot -i  # 找到搜索框的 ref
agent-browser fill @<搜索框ref> "口腔"
agent-browser keyboard Enter

# 4. 等待搜索结果加载
agent-browser wait --load networkidle

# 5. 抓取搜索结果
agent-browser eval "document.body.innerText"
```

## 什么时候搜

在 business-writing harness 的 Step 1c 阶段执行：
- 从需求中提取的检索词，同时去飞书搜索站搜索
- 重点关注"字节"相关的官方文档（如本地推产品手册、线索链路说明、广告投放规范等）

## 搜索结果的使用规则

1. **飞书文档的标题可以直接引用**——这些是字节官方对外文档，标题本身就是权威信息源
2. **如果有正文内容，可以提取具体策略/数据/链路描述**
3. **只有标题没有正文的文档**，可以引用标题作为"字节在该方向有官方文档"的证据，但不能引用正文细节
4. **引用时标注来源**："字节对外文档《XXX》"
