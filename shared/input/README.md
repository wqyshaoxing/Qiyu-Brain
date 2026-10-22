# shared/input

通用获取与筛选。目标是把「拿到可用材料」这件事和学科判断分开。

## 准入门槛

- 换任何一个领域都能原样使用。
- 输入输出是数据，不是观点。
- 失败可重试，且失败信息能定位到具体请求。

## 候选

| 候选 | 解决什么 | 前置 |
| --- | --- | --- |
| search-connectors | Crossref / arXiv / PubMed / Semantic Scholar 的统一适配，含限流与重试 | 无密钥优先 |
| doc-extract | PDF / HTML / DOCX → 结构化文本与图片，保留页码定位 | 可复用 MinerU 或 docling |
| web-capture | 网页快照与正文抽取，保留抓取时间与 URL | 需处理反爬与 robots |
| dedup-and-screen | DOI / 标题 / 全文多级去重，纳排留痕 | 依赖矩阵结构 |
| provenance-log | 每次取用写来源、时间、哈希 | 全阶段共用 |

## 不该放这里

- 某个学科特有的检索式构造（属于该领域 input）。
- 需要人工判断的纳排决策（属于 reasoning）。
