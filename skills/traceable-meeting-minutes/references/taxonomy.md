# 信息事件分类与压缩预算

读本文的时机:执行步骤 2(建语义账本)需要判断每条事件该归哪类、压到什么程度时。

## 信息事件分类(`type`)

| 值 | 中文 | 含义 |
|---|---|---|
| decision | 决策 | 已拍板的结论 |
| action | 行动项 | 谁 / 做什么 / 何时 |
| data | 数据 | 预算、指标、数量、日期 |
| risk | 风险 | 隐患、约束、红线 |
| qualifier | 限定条件 | "暂不""不得""仅限"等改变语义的修饰 |
| opinion | 观点 | 个人判断,未成结论 |
| case | 案例 | 具体故事/举例(最易被压没,最需保机制) |
| rebuttal | 反驳 | 对他人观点的反对 |
| open_question | 未决问题 | 当场没解决的问题 |
| revision | 原观点修正 | 某人对自己前面说法的更正 |
| background | 背景 | 重复铺垫,可高压缩 |
| chitchat | 寒暄 | 可高压缩 |

## 压缩预算(`compress`)

对应文章"不同信息,拥有不同的压缩预算"。

| 值 | 策略 | 适用 |
|---|---|---|
| zero | 接近零压缩:数字/日期/责任人/deadline/限定逐字保留 | decision, action, data, risk, qualifier |
| low | 轻度:保留论证与结论,去口水 | opinion, rebuttal, revision |
| mid | 谨慎:案例可缩短,但**必须保住机制/因果链** | case |
| high | 可高度压缩或仅归档 | background, chitchat |

`in_minutes`:是否进入正文。`false` 表示"本次不展示但已归档"——**绝不等于删除**,审计与 HTML 会列出并可找回。
