# academic-research

科研任务。覆盖从「这个方向有什么」到「投稿前引用别出错」。

## 边界

收：文献调研、证据整理、写作、图、引用审查、可复现性核对。
不收：数据采集设备的操作、投稿系统操作、经费与伦理审批流程——这些不是思考技能。
## 阶段与技能

入口在 `gateway/gateway-router`，先产出 `task_contract`。

| 阶段 | 技能 | 一句话 |
| --- | --- | --- |
| input | [academic-literature-search](input/academic-literature-search/SKILL.md) | 有界检索 + 留痕 + 去重，交付矩阵而不是链接堆 |
| input | [academic-zotero-archive](input/academic-zotero-archive/SKILL.md) | 把校验过的 PDF 归档进 Zotero，并核对真的进去了 |
| input | [academic-pdf-extract](input/academic-pdf-extract/SKILL.md) | PDF → full.md + 图片，提取源保持只读 |
| reasoning | [academic-claim-map](reasoning/academic-claim-map/SKILL.md) | 每条论断对上支持/反对/缺失证据，先暴露矛盾再写作 |
| output | [academic-paper-draft](output/academic-paper-draft/SKILL.md) | 只依据证据图写作，无证据的句子必须显式标注 |
| output | [academic-translate](output/academic-translate/SKILL.md) | 双语术语表 + 保真规则；fluent 但不等于原文的句子算错 |
| output | [academic-figure](output/academic-figure/SKILL.md) | 按「图要证明什么」选路线，交付可重跑的源文件 |
| output | [academic-latex-sync](output/academic-latex-sync/SKILL.md) | LaTeX ↔ Word 结构映射，公式与版式双侧核验 |
| verify | [academic-citation-audit](verify/academic-citation-audit/SKILL.md) | 逐条引用回原文核对，对不上就拦下 |

```text
gateway-router
  ├─ shared-scholarly-search ──→ academic-literature-search ──→ academic-claim-map ─┬─→ academic-paper-draft ─┬─→ academic-translate
  ├─ academic-zotero-archive ──→ academic-pdf-extract                                   │                 ├─→ academic-figure
  │                                                                  │                 └─→ academic-latex-sync
  └──────────────────────────────────────────────→ academic-citation-audit ←─ academic-paper-draft
```

## 与 BoomSkills 的分工

四个工具型技能已连同脚本搬入本仓库（`academic-zotero-archive`、`academic-pdf-extract`、`academic-latex-sync`，以及此前搬的翻译与绘图判断层）。脚本全部是**标准库实现**，复制后可直接运行，不依赖 BoomSkills 的运行时。

⚠️ 遗留：BoomSkills 里对应的 `zotero-batch-pdf-import`、`mineru-pdf-to-markdown`、`academic-latex-sync`、`academic-academic-translate`、`academic-figure-production` 现在是**重复能力**。按 `CONVENTIONS.md` 第 8 条，应在那几份顶部标「已迁移」或删除——尚未处理。

## 两条底线

1. 摘要不等于全文，全文不等于结论。证据层级必须随产物一起交付。
2. 没有任何一步可以因为「时间紧」跳过 verify。审稿人不会替你补。
