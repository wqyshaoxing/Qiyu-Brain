# 意图路由表

按「你嘴上会怎么说」查，不要按目录层级找。路径只服务人类浏览，触发靠 `description`。

## gateway（每次任务先走，不产出领域产物）

| 你可能会说 | 技能 | 产出 |
| --- | --- | --- |
| （任何请求开始前，包括看起来很简单的那种） | [task-router](gateway/task-router/SKILL.md) | task_contract、routing_decision、open_questions |
| 以后都这样 / 我不喜欢这种写法 / 记住我的偏好 | [preference-distillation](gateway/preference-distillation/SKILL.md) | profile_update → `_profile/` |

它必须在领域技能之前运行。跳过它，领域技能就在「完成」尚未定义的情况下开工了。

## academic-research

| 你可能会说 | 阶段 | 技能 | 主要产出 |
| --- | --- | --- | --- |
| 帮我查一下这个方向有哪些工作 / 建个文献矩阵 | input | [literature-search](academic-research/input/literature-search/SKILL.md) | query_plan、literature_matrix、search_log |
| 这些文献互相矛盾吗 / 我的论断有证据吗 | reasoning | [evidence-synthesis](academic-research/reasoning/evidence-synthesis/SKILL.md) | evidence_map、contradiction_log |
| 帮我写引言/方法/讨论 | output | [paper-draft](academic-research/output/paper-draft/SKILL.md) | draft、claim_index |
| 投稿前核一遍引用，别引错 | verify | [citation-evidence-audit](academic-research/verify/citation-evidence-audit/SKILL.md) | audit_report、evidence_bundle |

## coding

| 你可能会说 | 阶段 | 技能 | 主要产出 |
| --- | --- | --- | --- |
| 需求太模糊，先帮我把范围问清楚 | input | [requirement-intake](coding/input/requirement-intake/SKILL.md) | requirement_spec、open_questions |
| 这个功能该怎么设计 / 两个方案选哪个 | reasoning | [architecture-tradeoff](coding/reasoning/architecture-tradeoff/SKILL.md) | option_matrix、decision_record |
| 按这个 spec 实现 | output | [feature-implement](coding/output/feature-implement/SKILL.md) | patch、test_report、change_summary |
| 改完别把别的地方弄坏 | verify | [regression-gate](coding/verify/regression-gate/SKILL.md) | verification_report、residual_risks |

## livebetter

技能待落地，见 [领域说明](livebetter/README.md)。候选意图：目标与症状澄清、指南与证据检索、风险收益权衡、计划草案、就医红旗检查。

## 跨领域

`_core/` 目前只有契约与模板。出现**第二个领域**真的复用同一脚本时，才把它升进 `_core/`，见 [CONVENTIONS.md](CONVENTIONS.md)。

## shared（通用阶段分区，暂无技能）

跨领域复用、不绑定任务的能力放这里：`shared/input` 检索与抽取、`shared/reasoning` 证据分级与矛盾检测、`shared/output` 渲染与转换、`shared/verify` 引用核对与回归。四个阶段目录已建，**其中尚未放入技能**，准入条件见 [shared/README.md](shared/README.md)。

## 外部资源

不是技能，不进路由。想找现成实现或查某段思路的出处时看这里：

| 目的 | 位置 |
| --- | --- |
| 有哪些现成技能/插件/MCP 仓库可参考 | [third-party/registry.json](third-party/registry.json) |
| 我们某个技能借用了谁的代码或思路 | [third-party/provenance.json](third-party/provenance.json) |
| 许可红线与借用登记流程 | [third-party/README.md](third-party/README.md) |
