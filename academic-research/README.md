# academic-research

科研任务。覆盖从「这个方向有什么」到「投稿前引用别出错」。

## 边界

收：文献调研、证据整理、写作、图、引用审查、可复现性核对。
不收：数据采集设备的操作、投稿系统操作、经费与伦理审批流程——这些不是思考技能。

## 阶段与技能

入口在 `gateway/task-router`，它会先产出 `task_contract`；`literature-search` 消费该契约，不从零开始问需求。

| 阶段 | 技能 | 一句话 |
| --- | --- | --- |
| input | [literature-search](input/literature-search/SKILL.md) | 有界检索 + 留痕 + 去重，交付矩阵而不是链接堆 |
| reasoning | [evidence-synthesis](reasoning/evidence-synthesis/SKILL.md) | 每条论断对上支持/反对/缺失证据，先暴露矛盾再写作 |
| output | [paper-draft](output/paper-draft/SKILL.md) | 只依据证据图写作，无证据的句子必须显式标注 |
| output | [zh-en-translation](output/zh-en-translation/SKILL.md) | 双语术语表 + 保真规则；fluent 但不等于原文的句子算错 |
| output | [scientific-figure](output/scientific-figure/SKILL.md) | 按「图要证明什么」选路线，交付可重跑的源文件 |
| verify | [citation-evidence-audit](verify/citation-evidence-audit/SKILL.md) | 逐条引用回原文核对，对不上就拦下 |

依赖链：

```text
task-router
  └─ literature-search ──→ evidence-synthesis ──→ paper-draft ──┬─→ zh-en-translation
        │                        └──────────────────────→ scientific-figure
        └─ (检索由 shared/input/search-connectors 提供，也可由 agent 用别的办法完成)
```

## 与其他仓库的分工

**工具层在 BoomSkills**：文献获取（`paper-search`）、arXiv（`arxiv-mcp-server`）、Zotero 归档（`zotero-batch-pdf-import`）、PDF 解析（`mineru-pdf-to-markdown`）。这些是外部服务适配器，通过 `deps` 或工具路由使用，本目录不复制它们的代码。

**判断层在本仓库**：`zh-en-translation` 与 `scientific-figure` 改编自 BoomSkills 的同名技能（`academic-zh-en-translation`、`scientific-figure-production`），把术语保真规则和绘图路线选择搬了过来，但改成本仓库的契约形态（frontmatter + artifacts + completion）。

⚠️ 这意味着 BoomSkills 里那两份现在是**重复能力**。按 `CONVENTIONS.md` 第 8 条「同一能力不许两处存在」，应当把 BoomSkills 那两份标为已迁移或删除——这件事还没做。

## 两条底线

1. 摘要不等于全文，全文不等于结论。证据层级必须随产物一起交付。
2. 没有任何一步可以因为「时间紧」跳过 verify。审稿人不会替你补。
