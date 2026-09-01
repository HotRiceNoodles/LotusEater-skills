# 步骤 2–3 — 语义账本与分级压缩纪要

读本文的时机:transcript.json 就绪后,建账本、写纪要正文时。字段定义见 [references/data-contracts.md](../references/data-contracts.md),分类与压缩预算见 [references/taxonomy.md](../references/taxonomy.md)。

## 步骤 2 — 语义账本 (ledger.json)

**通读 transcript.json 全文**,把"真正发生过的信息事件"逐条登记成 ledger.json。每条含:`id`、`type`、`topic`、`quote`(逐字原话)、`start_sec/end_sec/seg_i`(回链)、`compress`(zero/low/mid/high)、`in_minutes`、`note`。

要点:
- **别把有价值的东西压成一句话**。像"多模态辅助儿童写作"这类 `case`,要保住它的机制/因果链(想象→写作→生成→发现差距→修改),不能只写"AI 辅助作文激发创作"。
- 每个决策、数据、行动项、风险、限定条件 → `compress:"zero"`,`quote` 逐字。
- 判断这次不进正文的事件,设 `in_minutes:false` 并写 `note` 说明,而不是丢弃。
- 遇到明显寒暄/重复背景才用 `high` 压缩或仅归档。

## 步骤 3 — 分级压缩生成纪要 (minutes.md)

写 Markdown 纪要(建议分节:结论/决策 → 行动项 → 关键讨论 → 案例与洞察 → 未决问题/风险)。**每条关键结论末尾挂 `[↩ Exx]`**,对应账本事件 id。零压缩类必须逐字带数字/日期/责任人/deadline。行动项单独成列表:谁—做什么—截止(缺任一标"待定",不臆造)。
