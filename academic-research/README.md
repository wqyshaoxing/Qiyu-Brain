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
| verify | [citation-evidence-audit](verify/citation-evidence-audit/SKILL.md) | 逐条引用回原文核对，对不上就拦下 |

## 与其他仓库的分工

文献获取、PDF 提取、Zotero 归档这类**工具型**能力在 BoomSkills，通过 `deps` 引用。本目录只放判断与流程，不复制那边的 `SKILL.md`。

## 两条底线

1. 摘要不等于全文，全文不等于结论。证据层级必须随产物一起交付。
2. 没有任何一步可以因为「时间紧」跳过 verify。审稿人不会替你补。
