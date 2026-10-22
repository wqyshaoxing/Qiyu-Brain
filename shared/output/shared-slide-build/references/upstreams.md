# 上游参考（PPT / 幻灯片）

2026-10-22 核实，三个仓库均为 MIT。

| 仓库 | commit | 形态 | 我们取用 |
| --- | --- | --- | --- |
| [mpuig/agent-slides](https://github.com/mpuig/agent-slides) | `820782a5fb` | 7 个可组合技能 + Python CLI | **判断层**：build 的流程与字数预算、audit 的技术+内容双通道、critique 的标题只读检查 |
| [siril9/presentation-skill](https://github.com/siril9/presentation-skill) | `efd899c5dd` | JSON 重建 + 原生图表 + 视觉 QA | **思路**：deck-spec 先行、按 spec 重建而不是改渲染结果 |
| [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | `604ecdec8d` | 单技能 + 分阶段角色切换 | **思路**：把长流程切成阶段并显式声明加载顺序 |

## 没取的

- 三个仓库的渲染实现（python-pptx、HTML→PDF、CLI 包装）。理由：本仓库的判断层与渲染器解耦，`shared-slide-build` 明确写「用什么渲染由 agent 决定」。
- `ppt-master` 的 13k 文件资产与 `requirements.txt` 依赖链。
- `agent-slides` 的 7 个技能没有逐一搬运：`extract`（从 pptx 抽模板契约）与 `edit`（就地改稿）目前没有需求，暂不引入。

## 关于重复

`agent-slides` 的 `slides-full` 是一条把 extract→build→audit→critique→polish 串起来的流水线。我们没有复制它，因为本仓库用 `deps` + `consumes`/`produces` 表达同样的串联关系——再写一个 full 技能等于把依赖图重说一遍。
