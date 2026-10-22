# 检索来源目录

调研日期 2026-10-22。「本机实测」是这台机器上真实发出的请求结果，**不是文档转述**。
「免费额度」一列的【官网】表示读过该站定价页，【汇总】表示读自第三方对比页，【未核实】表示凭记忆。

标记：✅ 免 key 可用 ｜ 🔑 需 key ｜ 🏠 需自建 ｜ ⛔ 不可达 ｜ ❌ 无免费额度 ｜ ⏸ 暂缓

| 来源 | 类型 | 认证 | 免费额度 | 本机实测 | 状态 |
| --- | --- | --- | --- | --- | --- |
| DuckDuckGo (lite) | 通用网页 | 无 | 无限 | 200，可解析 | ✅ 可用 |
| Wikipedia API | 百科 | 无 | 无限 | 200 | ✅ 可用 |
| Hacker News (Algolia) | 技术社区 | 无 | 无限 | 200，JSON | ✅ 可用 |
| StackExchange API | 技术问答 | 无 | 无限 | 200，JSON | ✅ 可用 |
| Exa | 神经检索 | `EXA_API_KEY` | **$10/月 + 注册 $10**，无需绑卡【官网】 | 402→ok | 🔑 已接入 |
| Tavily | AI 检索 | `TAVILY_API_KEY` | 1,000 credits/月【汇总】 | 401→ok | 🔑 已接入 |
| **Serper** | Google SERP | — | 2,500 次一次性，免绑卡【官网】 | 403→ok 实测可用 | ⏸ 暂缓（试过后不用） |
| Firecrawl | 检索+抓取 | `FIRECRAWL_API_KEY` | **1,000 credits/月 ≈ 500 次搜索**【官网】 | 500 | 🔑 已接入 |
| Google Programmable Search | Google 索引 | `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | **100 次/天**【官网】 | 403 | 🔑 已接入 |
| Linkup | 欧洲索引 | `LINKUP_API_KEY` | $20 注册额度（企业邮箱）【官网】 | 400 | 🔑 已接入 |
| Valyu | 科研/金融 | `VALYU_API_KEY` | $10 注册额度，12 个月有效【官网】 | 401 | 🔑 已接入 |
| LangSearch | 中英检索 | `LANGSEARCH_API_KEY` | **完全免费的免费计划**，按日 token 额度【官网】 | 400 | 🔑 已接入，结构待验证 |
| 博查 Bocha | 中文检索 | `BOCHA_API_KEY` | 试用 1,000 次 / 3 个月【汇总】 | 400 | 🔑 已接入，结构待验证 |
| Jina Search | 神经检索 | `JINA_API_KEY` | 有免费 token 额度【未核实】 | 403 | 🔑 已接入 |
| SearXNG（自建） | 元搜索 | `SEARXNG_URL` | 自建即免费 | 公共实例全 429/403 | 🏠 已接入 |
| Brave Search | 独立索引 | `BRAVE_API_KEY` | **$20/月**免费调用，预付制无订阅【官网】 | 422 | 🔑 已接入，待填（开通需支付方式验证） |
| **Kagi** | 付费搜索 | — | **无免费额度**，$12/1k requests【官网】 | 401 | ❌ 已移除 |
| **智谱 web_search** | 中文检索 | — | **无免费额度**【汇总】 | 401 | ❌ 已移除 |
| Bing Web Search | 通用网页 | — | — | 401，官方已退役 | ⛔ 不纳入 |
| Baidu | 中文网页 | 无公开 API | — | SSL 中断 | ⛔ 本网络不可用 |
| Sogou | 中文网页 | 无公开 API | — | JS 壳 | ⛔ 不可解析 |
| Bing (HTML) | 通用网页 | 无 | — | 结果与查询无关 | ⛔ 不可信 |
| Mojeek | 独立索引 | HTML 抓取 | — | 5.5KB 反爬页 | ⛔ 反爬 |
| Marginalia | 独立/小众 | 无 | — | API 超时 | ⛔ 不可用 |
| Startpage / 360 / Yandex XML | 通用网页 | 无公开 API | — | 未测 | ❓ 无可编程入口 |
| Common Crawl Index | 网页存档 | 无 | — | 超时 | ⛔ 本网络不可达 |
| Reddit search.json | 社区 | 无 | — | 403 | ⛔ 需 OAuth |
| arXiv / Crossref / OpenAlex / PubMed | 学术 | 无 | 无限 | 200 | ✅ 属 `search-connectors` |

## 有免费额度但尚未接入

评估过、可加但当前没写的来源：

| 来源 | 免费额度 | 接入成本 | 建议 |
| --- | --- | --- | --- |
| SerpApi | 250 次/月【汇总】；官网只列 $25 起付费档 | 低（GET，与 serper 同构） | 不必——Serper 已有 2,500 次 |
| 百度智能云千帆 | 100 次/天【汇总】 | 高（云账号鉴权、非简单 API key） | 中文刚需时再考虑 |
| 阿里云 IQS | 1,000 次 / 15 天试用【汇总】 | 高（阿里云签名） | 试用性质，不建议依赖 |
| Brave Search | $20/月【官网】 | 极低（已写过，可恢复） | 若需要独立索引，优先恢复它 |

## 移除与暂缓记录

2026-10-22 按「无免费额度」移除：

- **Kagi**：官网 [api/pricing](https://kagi.com/api/pricing) 写明 $12 / 1k requests，无免费层。
- **智谱 web_search**：[2026-03 搜索 API 价格汇总](https://hebangwen.github.io/2026/03/04/search-api-summary/) 标注无免费额度。

2026-10-22 曾按用户要求暂缓 **Brave Search**，同日恢复。它有 $20/月 免费额度，是当前付费源里额度最高的一个。
当前未填：开通需要绑定支付方式验证，用户暂不填。适配器保留，填 key 即可用。

2026-10-22 暂缓 **Serper**：用户实测后决定不用。适配器已删（PROVIDERS / FETCHERS / 函数 / ENV_KEYS 四处），
`.env` 与 `.env.example` 已清理。恢复方式与 Brave 相同，GET `google.serper.dev/search`，头 `X-API-KEY`。
注意它与 Google CSE 功能重复，两者取其一即可。

## 三条选型原则

1. 默认只跑四个免 key 源，覆盖通用网页、百科、技术社区、技术问答。
2. 付费源按需开启；缺 key 记 `skipped`，请求失败记 `failed`，绝不混为一谈。
3. 生成式检索（Perplexity 一类）不纳入：会把「答案」混进结果，破坏「摘要不等于事实」的边界。
