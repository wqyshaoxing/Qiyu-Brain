# 第三方技能包与本仓库的重叠分析

三个参考源（2026-10-22 核实 commit）：

| 仓库 | commit | 许可 | 技能数 | 定位 |
| --- | --- | --- | --- | --- |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | `593377bb0487` | MIT | 163 | 领域工具包装（biopython、astropy、rdkit…） |
| [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) | `c6ae86c74270` | Apache-2.0 | 20 | 科研全流程（nature-*） |
| [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | `3224a27a2571` | CC（含 NC/SA） | 4 | 写作与评审流程 |

**结论：三个都只作参考源，不打包引入。** 重叠部分保留我们自己的实现，理由见下。

## nature-skills 映射

| 他们的技能 | 我们的对应 | 处置 |
| --- | --- | --- |
| nature-academic-search | `literature-search` | 保留我们的（有 search-connectors 支撑） |
| nature-citation | `citation-evidence-audit` | 保留我们的 |
| nature-ref-verifier | `citation-evidence-audit` | 同上，可参考其核验清单 |
| nature-figure | `scientific-figure` | 保留我们的；绘图实现细节可参考 |
| nature-polishing | `zh-en-translation` | 保留我们的（有术语表与保真规则） |
| nature-writing | `paper-draft` | 保留我们的 |
| nature-reader | `pdf-extract` | 保留我们的（脚本已实测可跑） |
| nature-downloader | — | **缺口**：我们靠 BoomSkills 的 paper-search，未整合 |
| nature-reviewer | — | **缺口**：我们没有「以审稿人视角挑毛病」这一环 |
| nature-response | — | **缺口**：没有审稿意见回复（rebuttal）技能 |
| nature-data / nature-statistics | — | **缺口**：数据整理与统计判断没有对应物 |
| nature-experiment-log / paper-card / paper2ppt / image2ppt / paper-to-patent / proposal-writer / literature-pipeline / shared | — | 与本仓库当前焦点无关，暂不纳入 |

## academic-research-skills 映射

| 他们的技能 | 我们的对应 | 处置 |
| --- | --- | --- |
| academic-paper | `paper-draft` | 保留我们的 |
| academic-paper-reviewer | — | **缺口**，与 nature-reviewer 同类 |
| academic-pipeline | `gateway/task-router` + `deps` 链 | 保留我们的（依赖图即流水线） |
| deep-research | `literature-search` + `evidence-synthesis` | 保留我们的 |

## scientific-agent-skills

163 个技能里绝大多数是**领域计算工具**（结构生物学、天文、化学信息学），与本仓库的判断层不重叠。按分工它属于「工具层参考」：将来需要某个领域计算能力时，先查这里是否已有，而不是自己写。

## 因此"去掉"的是什么

1. **不引入**上述第三方技能的任何 `SKILL.md`——保留我们的版本，避免两套判断并存。
2. **不复制**它们的脚本；需要时按 `deps` 或工具路由调用。
3. 真正的重复在**本仓库与 BoomSkills 之间**：`zotero-import`、`pdf-extract`、`latex-word-sync`、`zh-en-translation`、`scientific-figure` 两边都有。BoomSkills 那五份已标注「已迁移」，本仓库为唯一维护版本。

## 值得补的四个缺口（按依赖图位置）

| 缺口 | 建议位置 | 为什么值得补 |
| --- | --- | --- |
| 审稿人视角自审 | `academic-research/verify/` | 现在 verify 只有引用核对，没有「论点是否站得住」 |
| 审稿意见回复 | `academic-research/output/` | 投稿后必经环节，目前完全空缺 |
| 数据与统计判断 | `academic-research/reasoning/` | 图与结论都依赖它，现在只有证据分级 |
| 文献下载 | `academic-research/input/` | 检索与归档之间少一环 |
