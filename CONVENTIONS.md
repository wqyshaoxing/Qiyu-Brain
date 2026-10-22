# 约定

## 层级

两种分区形态，各自固定层数：

```text
<domain>/<stage>/<skill>/     领域分区，三层
<gateway>/<skill>/            扁平分区，两层，仅 gateway 使用
```

- `domain`：任务领域，kebab-case，如 `academic-research`、`coding`、`livebetter`。
- `stage`：`input` / `reasoning` / `output` / `verify`。扁平分区不用阶段目录，改在 frontmatter 写 `stage: [gateway]`。
- `skill`：kebab-case，目录名必须等于 frontmatter 的 `name`。

技能目录内固定：

```text
SKILL.md
runtime.json
references/     可选
scripts/        可选，只在有可执行动作时建
```

## 五条硬规则

1. **一个技能只有一个家**。跨阶段用 `stage` 多值表达，跨领域用 `deps` 引用，绝不复制第二份 `SKILL.md`。
2. **`_core` 慎入**。第一次出现时留在使用它的领域里，第二个领域真的复用了才上移。过早抽象比重复更贵。
3. **阶段目录按需创建**。该领域该阶段没有技能，就不要建空目录加 `.gitkeep`。
4. **目录是给人看的，触发靠 `description`**。所以 `description` 要写「什么时候用」，不是「这个技能是什么」。
5. **链路靠契约，不靠目录顺序**。`consumes` / `produces` 必须能串起来；目录顺序不表达「先做 A 才能做 B」，真实思考是回环的。
6. **阶段 0 只有一个**。`gateway/` 是扁平分区，不套阶段目录；其技能必须 `stage: [gateway]`，不得产出领域产物。
7. **用户状态与技能分离**。画像和偏好在 `_profile/`，技能只读不写；写入走 `preference-distillation` 并留来源与置信度。
8. **外部仓库只登记不提交**。克隆体只能放 `third-party/repos/<id>/`；借用他人代码、思路、文本或数据，必须在 `third-party/provenance.json` 登记，并在该技能 frontmatter 的 `sources` 里声明 registry id。许可不明的上游只许借思路，不许复制代码。
9. **通用能力放 `shared/`，但别提前抽象**。只有同时满足「领域中立」和「至少两个领域会用」才进 `shared`；只有一个领域用的先留在该领域。依赖方向单向：领域技能可以 `deps` 指向 `shared`，反过来不允许。

## frontmatter

只允许标量或**行内列表**，方便零依赖解析：

```yaml
---
name: literature-search
description: 一句话，写触发场景，30–200 字符
domain: academic-research
stage: [input]
loop_role: entry
consumes: []
produces: [query_plan, literature_matrix, search_log]
deps: []
---
```

| 字段 | 必填 | 取值 |
| --- | --- | --- |
| `name` | 是 | kebab-case，等于目录名 |
| `description` | 是 | 自然语言，含触发场景 |
| `domain` | 是 | 等于所属领域目录名 |
| `stage` | 是 | 非空的 `[input\|reasoning\|output\|verify]`；领域分区须包含所在阶段目录，扁平分区须恰为 `[gateway]` |
| `loop_role` | 是 | `route` 路由 / `entry` 起点 / `transform` 加工 / `render` 成形 / `verify` 判定 |
| `consumes` | 是 | 上游 artifact role，可以是空列表 |
| `produces` | 是 | 本技能产出的 artifact role，可以为空但一般不空 |
| `deps` | 是 | 外部依赖（技能名、服务、`boomskills`），可以是空列表 |

## artifact role

- `snake_case`，名词或名词短语：`literature_matrix`、`evidence_map`、`verification_report`。
- role 是**跨技能接口**，改名前先搜 `consumes`。
- 详细规格（kind、是否必需、说明）只写在 `runtime.json` 的 `artifacts`，不在 frontmatter 重复。
- frontmatter `produces` 与 `runtime.json` artifacts 必须双向一致，`validate.py` 会查。

## runtime.json

```json
{
  "schema": 1,
  "mode": "agent",
  "actions": [],
  "artifacts": [
    {"role": "...", "kind": "markdown|csv|json|svg|patch|...", "required": true, "note": "验收时看什么"}
  ],
  "completion": {"requires_review": true, "hash_bound": true},
  "recovery": ["失败时怎么恢复"],
  "todo": ["还没落地的脚本动作"]
}
```

- `mode`: `agent`（当前宿主执行，无脚本）/ `script`（纯脚本）/ `hybrid`（两者都用）。
- `actions[].script` 声明的路径**必须真实存在**，否则校验失败——宁可写 `mode: agent` 也不许放假脚本。
- `completion.hash_bound` 为 true 时，验收必须提供绑定当前文件 SHA-256 的审查记录。

## 审查

审查记录与产物分开存，避免自证。

```json
{
  "passed": true,
  "checks": ["实际核对的内容与结论"],
  "limitations": ["仍存在的限制；没有则空数组"],
  "artifact_sha256": {"draft": "<sha256>"}
}
```

哈希只证明「审查的是这个版本」，不证明内容正确。语义验收仍要人或有上下文的 agent 做。

## 命名与语言

- 所有目录、role、action 名：`kebab-case` 或 `snake_case`，不用中文、空格、大写。
- `SKILL.md` 正文用英文（与 BoomSkills 一致，便于跨宿主复用）；仓库文档用中文。
- 不在技能、日志、交付物里写本机用户名、绝对私有路径、密钥、令牌。

## 隐私

公开示例只用合成数据。真实论文、客户代码、健康记录的路径与内容留在私有工作区，不进仓库。
