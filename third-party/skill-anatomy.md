# 现成搜索 skill 的解剖

调研目的：在写自己的搜索技能前，先看清别人**具体写了什么**、哪些章节反复出现、哪些是噪音。

方法：`git clone --depth 1` 到本地后逐文件阅读，不依赖二手转述。样本如下（行数为实测）。

| 仓库 / 文件 | 行数 | 定位 |
| --- | --- | --- |
| `exa-labs/exa-mcp-server` `skills/search/SKILL.md` | 207 | 研究编排器：分诊 + 子代理扇出 |
| `HKUSTDial/Supervisor-Skills` `skills/deep-research/SKILL.md` | 209 | 综述级：六道闸门 + 对抗式检索 |
| `upstash/context7` `skills/find-docs/SKILL.md` | 166 | 文档检索：库解析 + 配额处理 |
| `basic-memory` `skills/memory-research/SKILL.md` | 229 | 网页调研 → 结构化笔记 |
| `easygl1der/supervisor-skills-plus` `skills/research-core/SKILL.md` | 177 | 共享底座：规则 + 检查清单 |
| `mattpocock/skills` `skills/engineering/research/SKILL.md` | **12** | 极简：只写目标与交付物，其余交给后台 agent |
| `gpt-researcher` `skills/gpt-researcher/SKILL.md` | 12 | 同上，几乎只有一句「通过 MCP 做自主研究」 |

行数从 12 到 229，跨度近 20 倍。**长不代表好**：12 行那个把工作委派给后台 agent，规则写得少但每条都硬。

## 反复出现的章节

| 章节 | 出现于 | 具体写了什么 |
| --- | --- | --- |
| **Auth / Prerequisites** | exa、context7 | OAuth 优先、API key 次之、匿名可用但限流；关键是这句：认证失败时**告知修复方法，不要静默退回普通网页搜索** |
| **When to use / When NOT to use** | 全部 | 不只是「何时用」，更重要的是「何时不该用，该转给谁」 |
| **Query assessment** | exa | 按复杂度分 4 档；二义时**停下问用户**，给出两种解读和各自代价 |
| **Multi-pass 策略** | exa | 实体链式、先探后钻、先发现标准再找候选；每轮之间先合并去重 |
| **Source quality** | exa、basic-memory | 一手优于二手；官方文档/源码/规范优先；标注 as-of 日期 |
| **Hedging / as-of** | basic-memory | 「appears to be」「as of 2026-10」；没有一手来源不给精确数字；查不到就说查不到 |
| **Error handling** | context7 | 配额耗尽 → 告诉用户、建议认证、**不允许静默回退到训练数据**并假装查过 |
| **Common Mistakes** | context7 | 具体到可执行：ID 要带 `/` 前缀、用描述性查询而非单词、一次一个概念、查询里不放密钥 |
| **Gates / iteration** | HKUST | 六道闸门（角度/覆盖/引用/分类/校准/编织），各带严重级别与失败路由；「迭代到全部通过，深度由主题复杂度决定，不是固定轮数」 |
| **Privacy** | basic-memory | 查询会发给第三方，私人笔记内容不得进查询词 |
| **Boundaries with sibling skills** | HKUST | 明确写「这个技能不做什么，归哪个兄弟技能管」 |

## 值得抄的六条

1. **认证失败要说人话**：告诉用户缺哪个变量、去哪里申请，而不是换一个源硬凑。
2. **允许「查不到」是合法输出**：`not publicly available` 比编一个数字好。这条要写进契约，不只是写进提示。
3. **as-of 日期跟着结论走**：网页是快照，不是事实。日期要能支撑「以后按日期重新检索」。
4. **Common Mistakes 比 Workflow 更有用**：Workflow 说该做什么，Mistakes 说通常会错在哪。我们的 verify 层一直缺这个。
5. **查询词是外发数据**：密钥、私人笔记、未发表内容不能进 query。
6. **闸门要带失败路由**：「引用不实 → 回检索补证」，而不是「打回重做」。

## 不打算照抄的三条

1. **把编排塞进搜索技能**（exa 的 4 档分诊 + 子代理扇出）。我们的路由和严谨度定档在 `gateway/gateway-router`，搜索技能只做取数。理由：编排一旦写进每个技能，就会和路由重复且互相矛盾。
2. **六道闸门**。它适合「综述级交付」，不适合每次检索。我们把它挪到 verify 层按需启用。
3. **用 skill 承载工具文档**（context7 整篇是 CLI 用法）。工具用法应进 `references/`，SKILL.md 只留判断。

## 对我们 `shared-web-search` 的直接结论

现有 SKILL.md 只覆盖了「怎么跑」，缺了「怎么问、怎么信、怎么不泄露」。本轮补四块：query craft、source quality、hedging/as-of、common mistakes + privacy。
