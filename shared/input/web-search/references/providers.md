# 检索来源目录

调研日期 2026-10-22。「本机实测」是这台机器上真实发出的请求结果，**不是文档转述**。

标记：✅ 免 key 可用 ｜ 🔑 需 key（端点已确认可达） ｜ 🏠 需自建 ｜ ⛔ 不可达 ｜ ❓ 未测

| 来源 | 类型 | 认证 | 本机实测 | 状态 |
| --- | --- | --- | --- | --- |
| DuckDuckGo (lite) | 通用网页 | 无 | 200，12 条可解析 | ✅ 可用 |
| Wikipedia API | 百科 | 无 | 200 | ✅ 可用 |
| Hacker News (Algolia) | 技术社区 | 无 | 200，JSON | ✅ 可用 |
| StackExchange API | 技术问答 | 无 | 200，JSON | ✅ 可用 |
| GitHub Repos API | 代码仓库 | 无（token 更宽） | 200 | ❓ 未接入，属代码检索 |
| Exa | 神经检索 | `EXA_API_KEY` | 402（缺付费额度） | 🔑 已接入 |
| Tavily | AI 检索 | `TAVILY_API_KEY` | 401 | 🔑 已接入 |
| Brave Search | 独立索引 | `BRAVE_API_KEY` | 422（缺订阅头） | 🔑 已接入 |
| Serper | Google SERP | `SERPER_API_KEY` | 403 | 🔑 已接入 |
| Jina Search | 神经检索 | `JINA_API_KEY` | 403 | 🔑 已接入 |
| Firecrawl | 检索+抓取 | `FIRECRAWL_API_KEY` | 500（端点存活） | 🔑 已接入 |
| Linkup | 欧洲索引 | `LINKUP_API_KEY` | 400 | 🔑 已接入 |
| Valyu | 科研/金融 | `VALYU_API_KEY` | 401 | 🔑 已接入 |
| Kagi | 付费搜索 | `KAGI_API_KEY` | 401 | 🔑 已接入 |
| Google Programmable Search | Google 索引 | `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | 403 | 🔑 已接入 |
| 博查 Bocha | 中文检索 | `BOCHA_API_KEY` | 400（可达） | 🔑 已接入，响应结构待验证 |
| 智谱 web_search | 中文检索 | `ZHIPU_API_KEY` | 401 | 🔑 已接入，响应结构待验证 |
| LangSearch | 中英检索 | `LANGSEARCH_API_KEY` | 400 | 🔑 已接入，响应结构待验证 |
| SearXNG（自建） | 元搜索 | `SEARXNG_URL` | 公共实例全部 429/403 或 JSON 关闭 | 🏠 已接入 |
| Bing Web Search | 通用网页 | — | 401，但官方已宣布退役 | ⛔ 不纳入 |
| Baidu | 中文网页 | 无公开 API | SSL 中断 | ⛔ 本网络不可用 |
| Sogou | 中文网页 | 无公开 API | 200 但为 JS 壳 | ⛔ 不可解析 |
| Bing (HTML) | 通用网页 | 无 | 200 但结果与查询无关 | ⛔ 不可信 |
| Mojeek | 独立索引 | HTML 抓取 | 200 但页面 5.5KB 无结果 | ⛔ 反爬 |
| Marginalia | 独立/小众 | 无 | API 超时，HTML 无结果 | ⛔ 不可用 |
| Startpage / 360 / Yandex XML | 通用网页 | 无公开 API | 未测 | ❓ 无可编程入口 |
| Common Crawl Index | 网页存档 | 无 | 超时 | ⛔ 本网络不可达 |
| Reddit search.json | 社区 | 无 | 403 | ⛔ 需 OAuth |
| arXiv / Crossref / OpenAlex / PubMed | 学术 | 无 | 200 | ✅ 属 `search-connectors` |

## 接入状态

- **免 key 立即可用**：duckduckgo、wikipedia、hn、stackexchange。
- **需 key，适配器已写好**：exa、tavily、brave、serper、jina、firecrawl、linkup、valyu、kagi、google_cse、bocha、zhipu、langsearch。
- **需自建**：searxng。
- **只有 baidu 是「有适配器但本网络不可用」**，会如实报 failed，不会伪装成空结果。

## 三条选型原则

1. 默认只跑四个免 key 源，覆盖通用网页、百科、技术社区、技术问答。
2. 付费源按需开启；缺 key 记 `skipped`，请求失败记 `failed`，绝不混为一谈。
3. 生成式检索（Perplexity 一类）不纳入：它会把「答案」混进结果，破坏「摘要不等于事实」的边界。

## 与 SKILL.md 保持一致

`SKILL.md` 的 `--doctor` 会逐个来源实测，输出分三态：`ok` / `missing`（缺 key）/ `fail`（请求或解析失败，附原始响应片段）。
