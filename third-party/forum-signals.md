# 论坛与社区信号

记录调研中遇到的一手讨论。**只记标题级信号**：`web_fetch` 在本机被非公网 IP 策略阻断，无法读取帖子正文，因此下列内容不含正文引用，也不引用他人的具体论证。需要完整内容时请人工打开链接。

采集日期：2026-10-22

## 线索表

| 来源 | 线索 | 主题 | 对我们的意义 |
| --- | --- | --- | --- |
| r/ClaudeAI（经 aiweekly 转载） | [The More Skills You Add, the Faster Your Agent Might Die](https://aiweekly.co/node/2529) | 技能数量与 agent 性能的关系 | 直接支持「少而严」：技能越多，路由与上下文负担越重。对应我们的「按需创建目录」「严格完成契约」 |
| Hacker News | [Show HN: PolyMCP Skills](https://news.ycombinator.com/item?id=46770554) | MCP 工具的组织方式 | 工具规模化的分层问题，和 shared/ 的分区动机一致 |
| Hacker News | [Show HN: MCP-skill – generate Python skills from MCP servers](https://news.ycombinator.com/item?id=47274589) | 从 MCP server 自动生成 skill | 说明 MCP 与 skill 的边界正在融合；我们的 `actions.script` 是更可控的中间态 |
| V2EX | [留下你 vibe coding 中经常使用 Agent skills](https://global.v2ex.co/t/1195236) | 自用技能清单 | 中文社区的实际使用偏好，偏 coding 工作流 |
| V2EX | [除了 superpowers 还有哪些大家在用的 skill？](https://global.v2ex.co/t/1211917) | 替代品讨论，提到 mattpocock/skills、shanraisshan/claude-code-best-practice | 验证了这三个仓库的社区热度，已登记进 registry |
| V2EX | [Skill 用到 node.js 依赖，package.json 放哪？](https://global.v2ex.co/t/1191445) | 技能内依赖管理 | 工程细节痛点。我们的 `runtime.json` 用 `actions.requires` + `deps` 显式声明，避免歧义 |
| V2EX | [给你常用的 Website 做一个 Agent Skill](https://global.v2ex.co/t/1208455) | 把网站变成技能 | 与 `shared/input` 的 web-capture 候选重叠 |
| LobeHub（中文市集） | [Agent Skills 市集](https://lobehub.com/zh-TW/skills) | 技能分发平台，按用途分类 | 技能开始有「包管理 + 市集」形态，分发协议值得关注 |
| 知乎 | [暴涨 8 万 Star！TypeScript 大佬真实工程开发 Skills 开源](https://zhuanlan.zhihu.com/p/2039667875972118455) | 某 TS 项目开源 skills | 标题夸张，正文未读；指向的具体仓库未确认，**不据此登记任何条目** |
| BGR | [Claude Users Say These Are The Most Useful Skills](https://www.bgr.com/2277516/claude-users-say-these-are-most-useful-skills/) | 用户票选「最有用的技能」 | 二手转述，仅作热度参考 |
| 榜单 | [wind8ai/skills-top-stars](https://github.com/wind8ai/skills-top-stars) | 42 条按 star 排序的 skills 仓库 | 已全量抓取并逐条 `ls-remote` 核验存在性；**star 数值未核实**，且与其他来源不一致 |

## 五条结论

1. **最大争议是「技能数量」而不是「技能质量」。** 社区已经在担心技能堆多了反而降低 agent 表现。这和我们「一个技能只有一个家、按需创建目录、没有脚本就不许假装可执行」的克制设计方向一致，值得写成一条设计约束。
2. **分发形态正在标准化。** `claude plugin install`、skills.sh、LobeHub 市集——技能从「复制文件夹」走向「可安装包」。我们的 `install`/`_runtime` 自包含方案属于同一方向，但还缺版本号与依赖解析。
3. **MCP 与 skill 的边界在融合。** 既有「MCP 组织成 skill」，也有「从 MCP 自动生成 skill」。我们目前把 MCP 当适配器、把 skill 当判断，这个分层暂时还站得住，但需要盯住。
4. **中文社区偏实用清单，英文社区偏方法论。** V2EX 在讨论「装了什么、依赖怎么放」，HN 在讨论「组织与规模化」。两侧的痛点不同，我们的 `shared` vs 领域分区正好分别回应。
5. **热度与质量不相关。** 榜单前列有多个纯 README 索引仓库（4 个文件、无实现）。调研阶段必须区分「被讨论」和「有东西可学」。

## 待补

- 帖子正文与评论（需能访问外网的机器）。
- Reddit / HN 的点赞与评论数（`web_fetch` 被阻断）。
- Discord / X 上的讨论（无公开检索入口，暂缺）。
