# coding

开发任务。覆盖从「需求还没说清」到「改完没把别处弄坏」。

## 边界

收：需求澄清、方案权衡、实现、测试、回归、评审。
不收：环境安装、CI 配置、发布部署——这些属于运维技能，另建领域或引用外部技能。

## 阶段与技能

入口在 `gateway/gateway-router`，它会先产出 `task_contract`；`coding-requirement-intake` 消费该契约，不重复追问目标。

| 阶段 | 技能 | 一句话 |
| --- | --- | --- |
| input | [coding-requirement-intake](input/coding-requirement-intake/SKILL.md) | 把模糊需求变成可验收的 spec，含非目标 |
| reasoning | [coding-architecture-choice](reasoning/coding-architecture-choice/SKILL.md) | 用约束比较方案，记录决策与回退成本 |
| output | [coding-feature-build](output/coding-feature-build/SKILL.md) | 最小改动 + 测试 + 可核对的 diff 摘要 |
| verify | [coding-regression-gate](verify/coding-regression-gate/SKILL.md) | 先复现再修，跑测试矩阵，查夹带改动 |

## 与工具链的分工

`codex-provider-switch-repair` 这类宿主/工具修复技能留在 BoomSkills。本目录只管工程判断本身。

## 底线

- 没有复现就不算修好；没有失败案例的测试等于没测。
- diff 里出现 spec 之外的改动，必须在 `change_summary` 里主动说明，不能等评审发现。
