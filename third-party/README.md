# third-party

外部现成技能、插件、MCP 服务器和思路的来源清单。**只登记，不提交克隆体。**

```
third-party/
├─ registry.json     外部仓库清单（链接 + 是什么 + 有没有用 + 许可状态）
├─ provenance.json   本仓库技能借用他人代码/思路的引用详情
├─ repos/            克隆的仓库（已 gitignore，永不提交）
└─ .gitignore
```

## 为什么只登记不提交

一个热门 skill 仓库动辄几十 MB、上百个文件，克隆进来会把本仓库变成垃圾场，还有许可和供应链风险。需要时按 `registry.json` 里的链接现拉，拉下来的东西放在 `repos/` 里，用完删除。

**约定**：克隆路径必须是 `third-party/repos/<id>/`。校验器会检查 `local_path` 是否符合这个前缀——因为 `.gitignore` 只忽略 `repos/`，克隆到别处就会被提交。

## registry.json 字段

| 字段 | 说明 |
| --- | --- |
| `id` | kebab-case，唯一；克隆目录用它命名 |
| `name` | 展示名，通常 `owner/repo` |
| `url` | 必须 `https://` |
| `kind` | 类型：`official-skill-collection` / `skill-framework` / `skill-index` / `mcp-reference` / `mcp-index` / `subagent-collection` / `awesome-list` / `library` |
| `summary` | 一句话：这个仓库是什么 |
| `relevance` | 对我们哪个分区有用，或为什么没用 |
| `tags` | 检索用 |
| `status` | `listed` 仅登记 / `evaluating` 已克隆在评估 / `adopted` 已采用 / `rejected` 不采用 / `archived` 曾用已弃 |
| `license` / `license_checked` | 许可名与是否亲眼核对过。`license_checked: true` 时 `license` 不许是 `unknown` |
| `size` | `small` / `medium` / `large` / `unknown`。large 的建议只留链接 |
| `local_path` | 未克隆为 `null`；克隆后必须为 `third-party/repos/<id>` |
| `commit` | 克隆时锁定的 commit，避免上游变动导致结果不可复现 |
| `verified` | 是否实际打开仓库核对过元数据 |
| `added` | 登记日期 |

## 新增一条的流程

1. 先在 `registry.json` 里登记，`status: listed`，`license: unknown`，`verified: false`。
2. 需要深入时 `git clone <url> third-party/repos/<id>`，把 `status` 改 `evaluating`，`local_path` 和 `commit` 填上。
3. 核对 license 文件后改 `license` 与 `license_checked: true`。
4. 决定采用 → `adopted`，同时在 `provenance.json` 登记借用了什么。
5. 决定不用 → `rejected`，在 `relevance` 里写清为什么，避免以后重复评估。

## 借用必须登记

只要我们的技能用了别人的**代码、思路、文本、数据或设计**，就在 `provenance.json` 里加一条：

```json
{
  "registry_id": "obra-superpowers",
  "skill": "coding/reasoning/architecture-tradeoff",
  "kind": "idea",
  "what": "借用了「先写选项矩阵再决策」的流程结构，未复制文本",
  "files": [],
  "commit": "<上游 commit>",
  "url": "https://github.com/obra/superpowers",
  "license_at_copy": "MIT",
  "adapted": true,
  "date": "2026-10-22"
}
```

- `kind`：`code` / `idea` / `text` / `data` / `design`。
- `commit` 或 `url` 至少有一个，否则无法追溯。
- `adapted` 为 true 表示改写而非直接复制；两种都必须登记。
- 许可不明（`unknown`）的上游，只能借**思路**，不能复制代码或大段文本。校验器会在 `license_checked: false` 时报 warning。

## 许可红线

| 上游许可 | 能做什么 |
| --- | --- |
| MIT / Apache-2.0 / BSD | 可复制代码，保留版权声明与许可文本 |
| GPL / AGPL | 复制会把传染性带入本仓库，默认只借思路；确需复制必须先单独决策 |
| CC BY-NC-ND | **不可商用、不可演绎**。只能引用链接与事实性描述，不能复制清单文本、不能改写后分发 |
| 每子目录独立许可 | 逐个目录核对，不能因为根目录没有 LICENSE 就当成公有领域 |
| 无许可证 | 法律上默认保留所有权利：**只能读，不能复制**。借思路也要登记 |
| 不明 | 先按「无许可证」处理，直到亲眼看到 LICENSE 文件 |

## 与 BoomSkills 的区别

BoomSkills 是我们自己的另一个仓库，通过技能 `deps` 引用，不算 third-party；它不需要登记在这里。
