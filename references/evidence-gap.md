# 证据 / 假设 / 缺口 / 受阻来源

## 目的

使用此文件在证据不完整时保持报告的诚实性，并区分：
- 已有支撑的内容
- 推断的内容
- 仍需另一轮搜索的内容
- 现在需要人工协助的内容

## 定义

### 证据
直接由以下来源支撑的信息：
- 用户提供的材料
- 已检索到的公开外部来源（含微信公众号）
- 人工已提供的内部文档

### 假设
有助于报告推进但尚未完全验证的合理推断。
应谨慎撰写并明确标注。

### 缺口
可能仍可通过另一轮搜索解决的缺失输入。

### 受阻来源
看似重要但当前无法通过公开渠道获取的来源或数据点。例如：信息不存在于公开来源、原链接已失效、需要内部系统权限等。

## 要求的行为

当关键论点缺乏支撑时：
- 不要伪造确定性
- 不要将弱点模糊化为自信的表述
- 判断它是`缺口`还是`受阻来源`
- 对看起来仍可公开获取的缺口触发 `search`
- 对受阻来源触发 `blocked`

## 标准缺口模板

```md
### Gap N
- Gap:
- Why it matters:
- Best public path already tried:
- What is needed:
- Impact on current report:
```

## 标准受阻来源模板

```md
### Blocked Source N
- Item:
- Why it matters:
- Best public path already tried:
- Access blocker:
- Suggested human action:
- Impact on current report:
```
