# 检索来源目录

调研日期 2026-10-22。「本机实测」列是这台机器上实际发出的请求结果，**不是文档转述**。

标记：

- ✅ 现在就能用，无需 key
- 🔑 端点可达，但必须配置 key
- 🏠 需要自建实例
- ⛔ 实测不可达，或被反爬挡住
- ❓ 未实测，仅登记存在

| 来源 | 类型 | 认证 | 本机实测 | 结论 |
| --- | --- | --- | --- | --- |
| DuckDuckGo (lite) | 通用网页 | 无 | 200，12 条可解析 | ✅ 已接入 |
| Wikipedia API | 百科 | 无 | 200 | ✅ 已接入 |
| Hacker News (Algolia) | 技术社区 | 无 | 200，JSON | ✅ 已接入 |
| StackExchange API | 技术问答 | 无 | 200，JSON | ✅ 已接入 |
| GitHub Repos API | 代码仓库 | 无（有 token 则限流更宽） | 200 | ❓ 可用但未接入，属代码检索 |
| Exa | 神经检索 | `EXA_API_KEY` | 402（需付费额度） | 🔑 已接入 |
| Tavily | AI 检索 | `TAVILY_API_KEY` | 401 | 🔑 已接入 |
| Brave Search | 独立索引 | `BRAVE_API_KEY` | 422（缺订阅头） | 🔑 已接入 |
| Serper | Google SERP 转售 | `SERPER_API_KEY` | 403 | 🔑 已接入 |
| SearXNG（自建） | 元搜索 | `SEARXNG_URL` | 公共实例全部 429/403 或 JSON 关闭 | 🏠 已接入，需自建 |
| Jina Search (s.jina.ai) | 神经检索 | `JINA_API_KEY` | 403 | 🔑 未接入 |
| Firecrawl Search | 检索+抓取 | `FIRECRAWL_API_KEY` | 500（端点存活） | 🔑 未接入 |
| Perplexity Sonar | 检索+生成 | `PERPLEXITY_API_KEY` | 401 | 🔑 未接入（是生成式，不是纯检索） |
| Linkup | 欧洲索引 | `LINKUP_API_KEY` | 400 | 🔑 未接入 |
| Valyu | 科研/金融 | `VALYU_API_KEY` | 401 | 🔑 未接入 |
| Kagi | 付费搜索 | `KAGI_API_KEY` | 401 | 🔑 未接入 |
| Google Programmable Search | Google 索引 | `GOOGLE_CSE_KEY` + `CX` | 403 | 🔑 未接入，免费额度小 |
| LangSearch | 中文/英文 | `LANGSEARCH_API_KEY` | 400 | 🔑 未接入，响应结构待核 |
| 博查 Bocha | 中文检索 | `BOCHA_API_KEY` | 400（可达） | 🔑 未接入，中文场景优先候选 |
| 智谱 web_search | 中文检索 | `ZHIPU_API_KEY` | 401 | 🔑 未接入 |
| Bing Web Search | 通用网页 | — | 401，但官方已宣布退役 | ⛔ 不纳入新项目，需自行核实 |
| Baidu | 中文网页 | 无公开 API | SSL 中断 | ⛔ 本网络不可用；反爬严格 |
| Sogou | 中文网页 | 无公开 API | 200 但为 JS 壳 | ⛔ 不可解析 |
| Bing (HTML) | 通用网页 | 无 | 200 但结果与查询无关 | ⛔ 不可信 |
| Mojeek | 独立索引 | HTML 抓取 | 200 但页面 5.5KB 无结果 | ⛔ 反爬 |
| Marginalia | 独立/小众 | 无 | API 超时，HTML 无结果 | ⛔ 不可用 |
| Startpage / 360 / Yandex XML | 通用网页 | 无公开 API | 未测 | ❓ 无可编程入口 |
| Common Crawl Index | 网页存档 | 无 | 超时 | ⛔ 本网络不可达 |
| Reddit search.json | 社区 | 无 | 403 | ⛔ 需 OAuth |
| arXiv / Crossref / OpenAlex / PubMed | 学术 | 无 | 200 | ✅ 属 `search-connectors`，不重复接入 |

## 选型结论

1. **默认只跑四个免 key 源**：DuckDuckGo、Wikipedia、HN、StackExchange。覆盖通用网页、百科、技术社区、技术问答。
2. **付费源按需开启**：Exa（语义）、Tavily（AI 清洗）、Brave（独立索引）、Serper（Google）。
3. **中文检索的现成缺口**：百度、搜狗在本网络与反爬层面都不可用。唯一稳妥路径是自建 SearXNG 并指定 `engines=baidu`，或接入博查/智谱（需 key，且响应结构待验证）。
4. **不入库的**：生成式检索（Perplexity）会把答案混进结果，破坏「摘要不等于事实」的边界；退役 API 不引入。

## 待验证

- 博查、智谱、LangSearch 的真实响应结构（需要 key）。
- Linkup/Valyu 的免费额度与许可条款（未读官网，不做断言）。
- Bing API 的退役状态与替代品（本轮未核实清楚，故标 ⛔ 而非 ❌）。
