# 意图路由表

按「你嘴上会怎么说」查，不要按目录层级找。路径只服务人类浏览，触发靠 `description`。

## gateway（每次任务先走，不产出领域产物）

| 你可能会说 | 技能 | 产出 |
| --- | --- | --- |
| （任何请求开始前，包括看起来很简单的那种） | [gateway-router](gateway/gateway-router/SKILL.md) | task_contract、routing_decision、open_questions |
| 以后都这样 / 我不喜欢这种写法 / 记住我的偏好 | [gateway-preferences](gateway/gateway-preferences/SKILL.md) | profile_update → `_profile/` |

它必须在领域技能之前运行。跳过它，领域技能就在「完成」尚未定义的情况下开工了。

## academic-research

| 你可能会说 | 阶段 | 技能 | 主要产出 |
| --- | --- | --- | --- |
| 帮我查一下这个方向有哪些工作 / 建个文献矩阵 | input | [academic-literature-search](academic-research/input/academic-literature-search/SKILL.md) | query_plan、literature_matrix、search_log |
| 这些文献互相矛盾吗 / 我的论断有证据吗 | reasoning | [academic-claim-map](academic-research/reasoning/academic-claim-map/SKILL.md) | evidence_map、contradiction_log |
| 帮我写引言/方法/讨论 | output | [academic-paper-draft](academic-research/output/academic-paper-draft/SKILL.md) | draft、claim_index |
| 把查到的 PDF 归档进 Zotero，并核对真的进去了 | input | [academic-zotero-archive](academic-research/input/academic-zotero-archive/SKILL.md) | import_result、import_report |
| 这篇 PDF 帮我转成 markdown 和图片 | input | [academic-pdf-extract](academic-research/input/academic-pdf-extract/SKILL.md) | full_md、extraction_report |
| LaTeX 和 Word 两边要同步，别改错公式 | output | [academic-latex-sync](academic-research/output/academic-latex-sync/SKILL.md) | latex、word、manifest、qa |
| 帮我翻译成中/英文，别译走意思 | output | [academic-translate](academic-research/output/academic-translate/SKILL.md) | translated_draft、terminology_map、qa_record |
| 做一张能投出去的图 / 机制示意图 | output | [academic-figure](academic-research/output/academic-figure/SKILL.md) | figure_source、figure_preview、figure_qa |
| 投稿前核一遍引用，别引错 | verify | [academic-citation-audit](academic-research/verify/academic-citation-audit/SKILL.md) | audit_report、evidence_bundle |

## coding

| 你可能会说 | 阶段 | 技能 | 主要产出 |
| --- | --- | --- | --- |
| 需求太模糊，先帮我把范围问清楚 | input | [coding-requirement-intake](coding/input/coding-requirement-intake/SKILL.md) | requirement_spec、open_questions |
| 这个功能该怎么设计 / 两个方案选哪个 | reasoning | [coding-architecture-choice](coding/reasoning/coding-architecture-choice/SKILL.md) | option_matrix、decision_record |
| 按这个 spec 实现 | output | [coding-feature-build](coding/output/coding-feature-build/SKILL.md) | patch、test_report、change_summary |
| 改完别把别的地方弄坏 | verify | [coding-regression-gate](coding/verify/coding-regression-gate/SKILL.md) | verification_report、residual_risks |

## livebetter

技能待落地，见 [领域说明](livebetter/README.md)。候选意图：目标与症状澄清、指南与证据检索、风险收益权衡、计划草案、就医红旗检查。

## 跨领域

`_core/` 目前只有契约与模板。出现**第二个领域**真的复用同一脚本时，才把它升进 `_core/`，见 [CONVENTIONS.md](CONVENTIONS.md)。

## shared（通用阶段分区）

跨领域复用、不绑定任务的能力放这里，准入条件见 [shared/README.md](shared/README.md)。

| 你可能会说 | 阶段 | 技能 | 主要产出 |
| --- | --- | --- | --- |
| 帮我查一下有哪些论文 / 多源检索一遍 | input | [shared-scholarly-search](shared/input/shared-scholarly-search/SKILL.md) | query_plan、result_matrix、search_log |
| 上网查一下 / 最新的是什么 / 官方文档怎么说 | input | [shared-web-search](shared/input/shared-web-search/SKILL.md) | query_plan、result_matrix、search_log |

`shared/reasoning`、`shared/output`、`shared/verify` 三个阶段目录已建，**尚未放入技能**。

## 外部资源

不是技能，不进路由。想找现成实现或查某段思路的出处时看这里：

| 目的 | 位置 |
| --- | --- |
| 有哪些现成技能/插件/MCP 仓库可参考 | [third-party/registry.json](third-party/registry.json) |
| 我们某个技能借用了谁的代码或思路 | [third-party/provenance.json](third-party/provenance.json) |
| 许可红线与借用登记流程 | [third-party/README.md](third-party/README.md) |
