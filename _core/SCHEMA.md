# 技能契约规范

`scripts/validate.py` 就是本文的可执行版本。两者改一个必须同步改另一个。

## 目录与文件

```text
<domain>/<stage>/<skill>/     领域分区
├─ SKILL.md              必需，判断与流程
├─ runtime.json          必需，可执行契约
├─ references/           可选，长文、清单、模板
└─ scripts/              可选，确定性动作；声明的脚本必须存在

<gateway>/<skill>/            扁平分区，无阶段目录
├─ SKILL.md
└─ runtime.json
```

保留目录（不参与校验、不是技能）：`_core/`、`_memory/`、`_eval/`、`_profile/`、`scripts/`、`docs/`。

### 扁平分区

`gateway/` 是唯一的扁平分区，代表阶段 0。规则：

- 技能直接位于 `gateway/<skill>/`，不再套 `input/` 之类目录。
- frontmatter 必须写 `stage: [gateway]`，`loop_role` 用 `route` 或 `transform`。
- 领域分区里禁止出现 `gateway` 这个 stage 值。
- 分区内不得同时存在阶段目录和技能目录。

## SKILL.md

### frontmatter（YAML，行内列表）

```yaml
---
name: kebab-case
description: 触发导向的一句话
domain: kebab-case
stage: [input, reasoning]
loop_role: entry|transform|render|verify
consumes: [role, ...]
produces: [role, ...]
deps: []
---
```

校验规则：

| 编号 | 规则 | 级别 |
| --- | --- | --- |
| F1 | 文件以 `---` 开头，且能闭合 | error |
| F2 | `name`/`description`/`domain`/`stage`/`loop_role`/`consumes`/`produces`/`deps` 齐全 | error |
| F3 | `name` 为 kebab-case 且等于目录名 | error |
| F4 | `domain` 等于二级目录名 | error |
| F5 | `stage` 非空且都在枚举内（`input`/`reasoning`/`output`/`verify`/`gateway`） | error |
| F6 | 领域分区：所在阶段目录名 ∈ `stage`；扁平分区：`stage` 必须恰为 `[gateway]` | error |
| F7 | `loop_role` 在枚举内 | error |
| F8 | `description` 长度 30–200 | error / warn |
| F9 | 全仓 `name` 唯一 | error |
| F10 | `produces` 非空（除非明确标注为纯判定技能） | warn |

### 正文

至少包含这四个二级标题：

```text
## When to use
## Boundary
## Workflow
## Artifacts
```

`Boundary` 必须写「本技能明确不做什么」，这是防止越界替代推理的地方。`Workflow` 用编号步骤，每步写清判断条件和停止条件。

## runtime.json

```json
{
  "schema": 1,
  "mode": "agent",
  "actions": [],
  "artifacts": [],
  "completion": {"requires_review": true, "hash_bound": true},
  "recovery": [],
  "todo": []
}
```

| 编号 | 规则 | 级别 |
| --- | --- | --- |
| R1 | 文件是合法 JSON 对象 | error |
| R2 | `schema` 存在且为 `1` | error |
| R3 | `mode` ∈ `agent`/`script`/`hybrid` | error |
| R4 | `actions` 为数组；`mode: agent` 时通常为空 | warn |
| R5 | 每个 action 的 `script` 路径真实存在 | error |
| R6 | artifact 的 `role` 为 `snake_case`，且全文件唯一 | error |
| R7 | artifact 的 `required` 为布尔 | error |
| R8 | frontmatter `produces` ⊆ artifacts roles | error |
| R9 | 每个 `required: true` 的 artifact role ∈ `produces` | error |
| R10 | `completion.requires_review` 与 `hash_bound` 为布尔 | error |
| R11 | `mode` 非 `agent` 且 `actions` 为空 | warn |

### action 字段

| 字段 | 说明 |
| --- | --- |
| `name` | kebab-case，调用名 |
| `script` | 相对技能目录的脚本路径 |
| `external` | 是否联网/上传/写外部系统；为 true 时需用户显式授权 |
| `requires` | 依赖列表，如 `network`、`MINERU_API_KEY` |
| `effects` | 真实影响，一句话；`--plan` 展示用 |
| `plan_supported` | 是否支持只预览不执行 |

## 状态

```text
prepared → awaiting_agent → action_succeeded → completed
                            ↘ blocked / failed
completed → changed_after_review   （产物或审查记录被改动）
```

`action_succeeded` 只是脚本退出成功，**不是**技能完成。`completed` 需要：所有 required artifact 存在、结构合法、审查记录 `passed: true`、`artifact_sha256` 覆盖每个 required artifact 的当前哈希。

## 校验输出

```text
python scripts/validate.py
{"skills": 8, "errors": [], "warnings": []}
```

有 error 时退出码 1；只有 warning 时退出码 0。
