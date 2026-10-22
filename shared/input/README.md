# shared/input

通用获取与筛选。目标是把「拿到可用材料」这件事和学科判断分开。

## 准入门槛

- 换任何一个领域都能原样使用。
- 输入输出是数据，不是观点。
- 失败可重试，且失败信息能定位到具体请求。

## 候选

### 检索族（同一族内共享输出结构，可串可单用）

| 候选 | 解决什么 | 状态 |
| --- | --- | --- |
| [search-connectors](search-connectors/SKILL.md) | 学术 API 多源检索：arXiv / Crossref / OpenAlex / PubMed / Semantic Scholar / Exa | **已实现** |
| web-search | 通用网页检索（Exa / Tavily / Brave，按已配置 key 自动选择） | 待定 |
| code-search | 代码与实现检索：GitHub code search、grep.app、包注册表 | 待定 |
| doc-search | 指定文档站内的检索与版本对齐 | 待定 |
| feed-watch | 订阅源与更新追踪：RSS、arXiv 新文、仓库 release | 待定 |

族内约定：输出同一组 role（`query_plan` / `result_matrix` / `search_log`），上层可以无痛替换来源。

### 非检索类

| 候选 | 解决什么 | 前置 |
| --- | --- | --- |
| doc-extract | PDF / HTML / DOCX → 结构化文本与图片，保留页码定位 | 可复用 MinerU 或 docling |
| dedup-and-screen | DOI / 标题 / 全文多级去重，纳排留痕 | 依赖矩阵结构 |
| provenance-log | 每次取用写来源、时间、哈希 | 全阶段共用 |

## 不该放这里

- 某个学科特有的检索式构造（属于该领域 input）。
- 需要人工判断的纳排决策（属于 reasoning）。
