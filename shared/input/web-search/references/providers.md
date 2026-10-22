# 检索来源目录

调研日期 2026-10-22。「本机实测」是这台机器上真实发出的请求结果，**不是文档转述**。

标记：✅ 免 key 可用 ｜ 🔑 需 key（端点已确认可达） ｜ 🏠 需自建 ｜ ⛔ 不可达 ｜ ❌ 无免费额度（已移除）

| 来源 | 类型 | 认证 | 免费额度 | 本机实测 | 状态 |
| --- | --- | --- | --- | --- | --- |
| DuckDuckGo (lite) | 通用网页 | 无 | 无限 | 200，可解析 | ✅ 可用 |
| Wikipedia API | 百科 | 无 | 无限 | 200 | ✅ 可用 |
| Hacker News (Algolia) | 技术社区 | 无 | 无限 | 200，JSON | ✅ 可用 |
| StackExchange API | 技术问答 | 无 | 无限 | 200，JSON | ✅ 可用 |
| Exa | 神经检索 | `EXA_API_KEY` | 注册赠送（未核实额度） | 402（缺额度） | 🔑 已接入 |
| Tavily | AI 检索 | `TAVILY_API_KEY` | 1,000 credits/月 | 401 | 🔑 已接入 |
| Brave Search | 独立索引 | `BRAVE_API_KEY` | $5 credits/月 | 422 | 🔑 已接入 |
| Serper | Google SERP | `SERPER_API_KEY` | 注册赠送（未核实额度） | 403 | 🔑 已接入 |
| Jina Search | 神经检索 | `JINA_API_KEY` | 有免费 token（未核实额度） | 403 | 🔑 已接入 |
| Firecrawl | 检索+抓取 | `FIRECRAWL_API_KEY` | 有免费额度（未核实额度） | 500 | 🔑 已接入 |
| Linkup | 欧洲索引 | `LINKUP_API_KEY` | $20 注册额度（企业邮箱） | 400 | 🔑 已接入 |
| Valyu | 科研/金融 | `VALYU_API_KEY` | $10 注册额度，12 个月有效 | 401 | 🔑 已接入 |
| Google Programmable Search | Google 索引 | `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | 每日免费额度 | 403 | 🔑 已接入 |
| 博查 Bocha | 中文检索 | `BOCHA_API_KEY` | 试用 1,000 次 / 3 个月 | 400 | 🔑 已接入，结构待验证 |
| LangSearch | 中英检索 | `LANGSEARCH_API_KEY` | 完全免费的免费计划 | 400 | 🔑 已接入，结构待验证 |
| SearXNG（自建） | 元搜索 | `SEARXNG_URL` | 自建即免费 | 公共实例全 429/403 | 🏠 已接入 |
| **Kagi** | 付费搜索 | — | **无免费额度**，$12/1k requests | 401 | ❌ **已移除** |
| **智谱 web_search** | 中文检索 | — | **无免费额度** | 401 | ❌ **已移除** |
| Bing Web Search | 通用网页 | — | — | 401，官方已退役 | ⛔ 不纳入 |
| Baidu | 中文网页 | 无公开 API | — | SSL 中断 | ⛔ 本网络不可用 |
| Sogou | 中文网页 | 无公开 API | — | 200 但为 JS 壳 | ⛔ 不可解析 |
| Bing (HTML) | 通用网页 | 无 | — | 200 但结果无关 | ⛔ 不可信 |
| Mojeek | 独立索引 | HTML 抓取 | — | 200 但 5.5KB 无结果 | ⛔ 反爬 |
| Marginalia | 独立/小众 | 无 | — | API 超时 | ⛔ 不可用 |
| Startpage / 360 / Yandex XML | 通用网页 | 无公开 API | — | 未测 | ❓ 无可编程入口 |
| Common Crawl Index | 网页存档 | 无 | — | 超时 | ⛔ 本网络不可达 |
| Reddit search.json | 社区 | 无 | — | 403 | ⛔ 需 OAuth |
| arXiv / Crossref / OpenAlex / PubMed | 学术 | 无 | 无限 | 200 | ✅ 属 `search-connectors` |

## 移除记录

2026-10-22：按「一点免费额度都没有」的标准移除两个来源，代码、`.env.example`、`config/schema.json` 三处同步删除。

- **Kagi**：官网 [api/pricing](https://kagi.com/api/pricing) 写明 $12 / 1k requests，按量付费，无免费层。
- **智谱 web_search**：[2026-03 搜索 API 价格汇总](https://hebangwen.github.io/2026/03/04/search-api-summary/) 标注其无免费额度。

保留 Exa（用户指定）。其余付费来源均至少有注册赠送或月度额度。

## 接入状态

- **免 key 立即可用**：duckduckgo、wikipedia、hn、stackexchange。
- **需 key，适配器已写好**：exa、tavily、brave、serper、jina、firecrawl、linkup、valyu、google_cse、bocha、langsearch。
- **需自建**：searxng。
- **有适配器但本网络不可用**：baidu，会如实报 `failed`，不伪装成空结果。

## 三条选型原则

1. 默认只跑四个免 key 源，覆盖通用网页、百科、技术社区、技术问答。
2. 付费源按需开启；缺 key 记 `skipped`，请求失败记 `failed`，绝不混为一谈。
3. 生成式检索（Perplexity 一类）不纳入：它会把「答案」混进结果，破坏「摘要不等于事实」的边界。

## 价格数据的可信度

「免费额度」一列中，Tavily / Brave / Linkup / Valyu / LangSearch 读自各自官网定价页；博查读自第三方汇总；其余标注「未核实」的是凭记忆，**采用前请以官网为准**。
