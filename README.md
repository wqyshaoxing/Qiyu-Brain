# Qiyu-Brain

把「一个科研工作者和开发者实际怎么做事」拆成可安装、可验收的技能仓库。

不是流水线，是回环：input 的检索会被 reasoning 的怀疑打断，verify 的发现会退回 input 补证。所以目录只按**分区**组织，**阶段写进元数据**——同一个能力不会为了结构整齐被复制几份。

## 四类目录

| 目录 | 是什么 | 形态 |
| --- | --- | --- |
| `gateway/` | 阶段 0：读画像、消歧、定验收、选路由 | 扁平分区，技能直接挂一层 |
| `academic-research/`、`coding/`、`livebetter/` | 任务领域 | 领域 / 阶段 / 技能，三层 |
| `third-party/` | 外部现成技能与仓库的登记清单，只存链接不存代码 | 不是技能，不参与路由 |
| `_core/`、`_memory/`、`_eval/`、`_profile/` | 契约、沉淀、样例、用户状态 | 不是技能，不参与路由 |

`_profile/` 是**状态**不是技能：你的身份、偏好、硬约束。技能只读它，写入必须走 `preference-distillation` 并留下来源。

## 结构

```text
Qiyu-Brain/
├─ gateway/                阶段 0，扁平分区
│  ├─ task-router/
│  └─ preference-distillation/
├─ academic-research/      领域分区
│  ├─ input/  reasoning/  output/  verify/     ← 阶段目录，按需创建
├─ coding/
├─ livebetter/             骨架，契约已定义，阶段目录待建
├─ _core/                  契约与模板
│  ├─ SCHEMA.md
│  └─ templates/
├─ _memory/                跨任务沉淀，验证过的结论才许进
├─ _profile/               用户画像与偏好
├─ third-party/            外部仓库清单，只登记不提交克隆体
│  ├─ registry.json        链接、简介、许可状态、评估结论
│  └─ provenance.json      本仓库借用他人代码/思路的引用详情
├─ _eval/                  回归样例与失败样例
├─ INDEX.md                任务意图 → 技能 的路由表
├─ CONVENTIONS.md          命名、层级、契约硬规则
└─ scripts/validate.py     无第三方依赖的结构校验
```

## 阶段 0：gateway

任何请求进来先过 `task-router`：读 `_profile/` → 复述并消歧 → 定严谨度档位 → 选领域与入口技能 → 出契约 → 复述确认。没有这一步，领域技能会在「完成」没被定义的情况下开工。

它刻意不放进任何领域：放进去就要复制四份，放进 `_core` 又会被当成工具库忽略。

## 四个阶段（领域内）

| 阶段 | 做什么 | 自检问题 |
| --- | --- | --- |
| input | 明确与拓展渠道、检索、调研、获取下载、查重去冗、筛选、留痕 | 三个月后别人能重跑这次检索吗？ |
| reasoning | 分析、联系、挖掘、排查谬误与造假、拓展、对比、评估 | 有没有哪条论断我没有对应的证据？ |
| output | 创作、撰写、绘图、编辑 | 产物能不能被独立核对，而不是只能信我？ |
| verify | 复现、复核、审查、分级证据、回归 | 如果我是审稿人/评审，会不会拒？ |

`output` 不等于完成。状态上区分 `prepared` / `action_succeeded` / `completed`，只有产物齐全且审查记录了当前文件哈希，才算 `completed`。

## 快速开始

```text
python scripts/validate.py
```

输出 `{"skills": N, "errors": [], "warnings": []}`。有 error 时退出码为 1。

## 新增一个技能

1. 判断它属于哪个分区、主阶段是哪个（跨阶段写多个值，但仍然只放一个目录）。
2. 只有该领域在该阶段已有 ≥2 个技能时，才建新的阶段目录；否则别建。
3. 建目录：领域用 `domain/<stage>/<kebab-name>/`，gateway 用 `gateway/<kebab-name>/`。
4. 从 `_core/templates/` 复制 `SKILL.md` 与 `runtime.json`，填 `consumes` / `produces`。
5. 在 `INDEX.md` 登记一行，并在 `_eval/` 放至少一个 fixture。
6. 跑 `validate.py`；有可执行动作时，脚本必须真的存在。

## 与 BoomSkills 的关系

**不重写执行层。** BoomSkills 的 `runs/`、`status`、`finish`、审查哈希绑定已经完整，Qiyu-Brain 复用那套 runtime：

- 领域技能包（文献检索、PDF 提取、Zotero 归档等）由 BoomSkills 提供，通过 `deps` 引用，**不搬 SKILL.md 过来**。
- Qiyu-Brain 只负责认知层与跨领域原语。
- 同一能力在两个仓库同时存在，是不允许的。

## 现状

- 10 个契约骨架：gateway 2 个、academic-research 4 个、coding 4 个。全部 `mode: agent`，**尚无脚本动作**；`runtime.json` 的 `todo` 写明要落地的动作。
- third-party 登记了 8 个外部仓库，**已全部通过 git 实测核实**：HEAD commit、LICENSE、文件数。star 与最近提交时间未核对（`web_fetch` 拒绝非公网 IP）。`provenance.json` 目前为空。
- livebetter 只有领域边界与安全契约，未建阶段目录。
- 仓库尚未 `git init`。
