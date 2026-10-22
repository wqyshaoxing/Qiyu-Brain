# Qiyu-Brain

把「一个科研工作者和开发者实际怎么做事」拆成可安装、可验收的技能仓库。

不是流水线，是回环：input 的检索会被 reasoning 的怀疑打断，verify 的发现会退回 input 补证。所以目录只按**分区**组织，**阶段写进元数据**——同一个能力不会为了结构整齐被复制几份。

## 五类目录

| 目录 | 是什么 | 形态 |
| --- | --- | --- |
| `gateway/` | 阶段 0：读画像、消歧、定验收、选路由 | 扁平分区，技能直接挂一层 |
| `shared/` | 跨领域通用能力：检索连接器、文档抽取、去重、证据分级、渲染、核验 | 领域 / 阶段 / 技能，三层，但技能必须领域中立 |
| `academic-research/`、`coding/`、`livebetter/` | 任务领域 | 领域 / 阶段 / 技能，三层 |
| `third-party/` | 外部现成技能与仓库的登记清单，只存链接不存代码 | 不是技能，不参与路由 |
| `_core/`、`_memory/`、`_eval/`、`_profile/` | 契约、沉淀、样例、用户状态 | 不是技能，不参与路由 |

`_profile/` 是**状态**不是技能：你的身份、偏好、硬约束。技能只读它，写入必须走 `gateway-preferences` 并留下来源。

## 结构

```text
Qiyu-Brain/
├─ gateway/                阶段 0，扁平分区
│  ├─ gateway-router/
│  └─ gateway-preferences/
├─ shared/                 通用阶段分区，跨领域复用（技能暂缺）
│  ├─ input/  reasoning/  output/  verify/
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

任何请求进来先过 `gateway-router`：读 `_profile/` → 复述并消歧 → 定严谨度档位 → 选领域与入口技能 → 出契约 → 复述确认。没有这一步，领域技能会在「完成」没被定义的情况下开工。

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

## 体系：靠依赖，不靠封装

本项目**只做技能**，不提供 MCP server，也不做宿主插件。体系边界写在 `SKILL.md` 里：

`yaml
deps: [gateway-router]        # 前置技能
consumes: [task_contract]  # 上游产物角色
produces: [query_plan, result_matrix, search_log]
`

| 字段 | 含义 | 谁来校验 |
| --- | --- | --- |
| `deps` | 需要先存在哪个技能 | `validate.py`：必须存在、不许成环、`shared` 只能依赖 `shared`、**且必须在正文出现** |
| `consumes` / `produces` | 数据流契约，靠 role 名对接而不是文件名 | `validate.py`：被消费的 role 必须有人产出（外部输入除外） |
| 正文 `## Requires` | 给模型看的前置条件 | 模型只读正文，frontmatter 里写了也没用 |

当前依赖图：

`	ext
gateway-router ─┬─ academic-literature-search → academic-claim-map → academic-paper-draft → academic-citation-audit
             ├─ coding-requirement-intake → coding-architecture-choice → coding-feature-build → coding-regression-gate
             └─ gateway-preferences

shared-scholarly-search   (独立)
shared-web-search          (独立)
`

**调用方式由 agent 决定。** 技能声明要什么、给什么、什么算完成，不规定用哪个工具、拼哪条命令。`runtime.json` 里的脚本是**参考实现**，不是唯一路径。

## 生命周期

`	ext
python scripts/qiyu.py build                     # 打平到 dist/（generic / agents / claude）
python scripts/qiyu.py install --host dsh --root <skills-root> [--force]
python scripts/qiyu.py adopt --host dsh --root <skills-root>   # 登记已有安装，不拷贝
python scripts/qiyu.py status                    # 已装版本 vs 源码、漂移、缺失、未跟踪
python scripts/qiyu.py doctor                    # 脚本参数一致性 + 凭据覆盖
python scripts/qiyu.py uninstall --host dsh      # 只删记录过的目录
`

状态记在 `.qiyu/state.json`（gitignore），不写进宿主技能根，宿主只看到技能目录。

`status` 区分四种状态：`insync` / `source-newer`（源码改了、装的是旧的）/ `modified`（安装副本被改过）/ `missing`。有漂移时退出码为 1。

## 装进 DSH

DSH 的技能发现顺序（源码实测）：

| 优先级 | 来源 | 路径 |
| --- | --- | --- |
| 100 | project-dsh | `<projectRoot>/.dsh/skills` |
| 200 | project-agents | `<projectRoot>/.agents/skills` |
| 300 | custom | `Config.customSkillDirs` |
| 400 | user-dsh | `<dshHome>/skills` |
| 500 | user-agents | `<agentsHome>/skills` |

`projectRoot` 是最近的含 `.git` 的祖先；没有就用当前目录。`watch` 默认开启，装进去即被发现，无需重启。

装完注意两点：

1. **配置要能被找到**。安装位置离仓库很远，`.env` 不在向上搜索链里。用 `QIYU_ENV_FILE` 指向它，或复制成 `~/.dsh/qiyu.env`。
2. **改源码后要重装**。安装是复制而非链接，`--force` 才会覆盖；`status` 会告诉你哪些落后了。
## 与 BoomSkills 的关系

**不重写执行层。** BoomSkills 的 `runs/`、`status`、`finish`、审查哈希绑定已经完整，Qiyu-Brain 复用那套 runtime：

- 领域技能包（文献检索、PDF 提取、Zotero 归档等）由 BoomSkills 提供，通过 `deps` 引用，**不搬 SKILL.md 过来**。
- Qiyu-Brain 只负责认知层与跨领域原语。
- 同一能力在两个仓库同时存在，是不允许的。

## 现状

- 10 个契约骨架：gateway 2 个、academic-research 4 个、coding 4 个。全部 `mode: agent`，**尚无脚本动作**；`runtime.json` 的 `todo` 写明要落地的动作。
- `shared/` 已落两个基石技能：`shared-scholarly-search`（六源学术检索）与 `shared-web-search`（网页检索，当前 7 个可用源）。都只用标准库，都能脱离路由单独跑。
- Zotero 与 MinerU 的 key 已配置，但消费方是 BoomSkills 的 `zotero-batch-pdf-import` 与 `mineru-pdf-to-markdown`；Qiyu-Brain 通过 `config/schema.json` 的 `skills` 字段指向外部技能，不重复实现。
- `third-party/skill-anatomy.md` 记录了 7 个现成搜索 skill 的解剖结论：哪些章节反复出现、哪 6 条值得抄、哪 3 条不抄。
- third-party 登记 **86 个外部仓库**：47 个已深核（commit + LICENSE + 文件数 + SKILL.md 数量），39 个仅核存在性（`git ls-remote`）。star 数无法核实（`web_fetch` 拒绝非公网 IP）。`provenance.json` 目前为空。
- `third-party/forum-signals.md` 记录了论坛线索与五条结论，仅到标题级——帖子正文未能读取。
- `scripts/build_plugin.py` 可把源码树打成 `generic` / `agents` / `claude` 三种宿主包，产物自包含、无密钥；`claude` 的布局尚未在真实宿主验证。
- livebetter 只有领域边界与安全契约，未建阶段目录。
- 仓库已 `git init` 并推送到 `origin/main`。
