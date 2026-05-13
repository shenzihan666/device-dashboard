# 参考项目索引（references/INDEX.md）

> 本目录收纳所有外部参考项目。每个子目录是一个独立的开源仓库克隆（或 vendored
> 副本），配套一个 `.study-meta.md`（元数据）和 `LEARNING_PLAN.md`（学习与
> 落地计划）。

## 索引表

| 仓库名 | 焦点（Phase 1.2） | 借鉴层级（Phase 1.3） | License | 加入日期 | 最近更新 | 状态 |
|--------|--------------------|------------------------|---------|----------|----------|------|
| _示例: `awesome-project`_ | _测试策略_ | _B 借鉴模式_ | _MIT_ | _2026-05-08_ | _2026-05-08_ | _进行中_ |

> 表格按「最近更新」倒序排列。新增一行时请放在示例行下方。

## 复用约定

- 重新参考某个项目：直接告诉 Cursor「再看一下 `<repo-name>`」或「继续学
  `<repo-name>` 的 <focus>」，Cursor 会自动读取 `INDEX.md` + 该项目的
  `.study-meta.md` + `LEARNING_PLAN.md` 恢复上下文，无需重新克隆。
- 新增一个参考项目：告诉 Cursor「想参考一下 `<GitHub URL>`」即可，Cursor
  会按 `learnfrom` 技能的 6 步流程跑一遍。
- 状态字段：
  - **进行中** — 正在 Phase 3-5 之间
  - **已落地** — 学习计划中的关键点都已移植到本项目
  - **已归档** — 不再使用，但保留以备查阅

## License 速查

详见每个项目下 `LEARNING_PLAN.md` 中的「License & 合规说明」一节，以及
`references/<repo>/LICENSE`（vendored 项目必须保留此文件）。
