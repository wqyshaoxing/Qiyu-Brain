# shared（通用阶段分区）

跨领域复用、不绑定具体任务的技能。一个检索连接器、一个去重流程、一个引用核对器，不应该在 academic-research、coding、livebetter 里各写一遍。

## 与其它分区的分工

| 分区 | 是什么 | 例子 |
| --- | --- | --- |
| `gateway/` | 阶段 0：路由与契约 | gateway-router |
| `shared/` | 通用动作，**可执行** | 通用检索适配器、文档抽取 |
| `academic-research/` 等 | 领域动作 | academic-literature-search（带学科纳排标准） |
| `_core/` | 文档契约与模板，**不可执行** | SCHEMA.md |

## 准入条件（三条都要满足）

1. **领域中立**：description 和边界里不出现论文、代码、体检、合同这类词。出现即说明它属于某个领域。
2. **至少两个领域会用**：只有一个领域会用的，先留在那个领域里，不要提前抽象。
3. **不重复造**：上游已有成熟实现（BoomSkills 或第三方）时，用 `deps` 引用，不在 `shared` 里再写一份。

## 与领域技能的关系

领域技能通过 `deps: [shared 的技能名]` 引用；共享技能不反过来依赖任何领域技能。这条是单向的，`validate.py` 会检查 `deps` 指向的名字真实存在。

## 阶段目录

| 阶段 | 放什么 |
| --- | --- |
| `input/` | 获取与筛选：检索连接器、抓取、抽取、去重、留痕 |
| `reasoning/` | 通用判断：证据分级、矛盾检测、谬误清单、方案对比 |
| `output/` | 成形：渲染、转换、导出、翻译 |
| `verify/` | 核验：引用核对、可复现性、回归、哈希 |

## 定位：基石层

`shared/` 不是「杂项」目录，是**其它技能的地基**。三层单向：`gateway → shared → 领域`。

只有 `shared` 能被所有领域安全依赖，所以它必须自己干净：

- 只依赖 `shared` 内的技能，绝不反向依赖某个领域。
- 只用标准库；确需第三方包时在 `actions[].requires` 声明，缺依赖明确报错。
- 发布的接口要稳：artifact roles、脚本 CLI 参数、退出码、失败语义。改这些等于改公共 API。

## 基石 skill 的四件交付物

| 交付物 | 位置 | 谁用 |
| --- | --- | --- |
| artifact roles | `runtime.json` 的 `artifacts` | agent 层串联 |
| 脚本入口 | `scripts/*.py` + 稳定 CLI | 程序层调用 |
| 失败语义 | `runtime.json` 的 `recovery` | 上层决定重试还是上报 |
| 依赖声明 | `actions[].requires` | 构建与 doctor 检查 |

## 安装后的复用

技能装到宿主目录后是独立副本，跨技能 `import` 会断。复用只发生在源码层：构建时把基础库 vendoring 进每个安装包，产物自包含。落地在 `scripts/build_plugin.py`（待建）。

## 现状

| 阶段 | 技能 | 说明 |
| --- | --- | --- |
| input | [shared-scholarly-search](input/shared-scholarly-search/SKILL.md) | 六源检索、有界重试、DOI 级去重、三者产物留痕。标准库实现，无依赖 |
| input | [shared-web-search](input/shared-web-search/SKILL.md) | 十源网页检索、按 URL 与标题两轮去重、噪声页过滤 |
| reasoning | — | 候选见 [reasoning/README.md](reasoning/README.md) |
| output | [shared-slide-build](output/shared-slide-build/SKILL.md) | 论点脊柱 → 标题大纲 → 字数预算 → 版式原型 → spec 先行渲染 |
| verify | [shared-slide-audit](verify/shared-slide-audit/SKILL.md) | 技术通道（字号/溢出）+ 内容通道（标题是否声明论断）+ 标题只读检查 |

其余阶段按需创建技能，不预建空壳。
