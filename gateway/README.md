# gateway（扁平分区）

不是任务领域，是**入口**。任何请求进入领域技能前先过这里：读长期画像、消除歧义、定验收、选路由。

## 为什么允许不套阶段目录

它没有 `input` / `reasoning` / `output` / `verify` 四阶段——它本身就是阶段 0。所以这个分区是**扁平**的：技能直接是 `gateway/<skill>/`，frontmatter 写 `stage: [gateway]`、`loop_role: route`。

校验器认两种分区形态：有阶段目录的（领域）和扁平的（gateway）。扁平分区里的技能 stage 必须是 `[gateway]`，领域里不许出现 `gateway`。

## 与 `_profile` 的分工

| | 是什么 | 谁改 |
| --- | --- | --- |
| `gateway/` | **行为**：怎么问、怎么定契约、怎么路由 | 开发者维护 |
| `_profile/` | **状态**：你是谁、偏好什么、硬约束 | 用户随时手改，以手改为准 |

## 技能

| 技能 | 作用 | 产出 |
| --- | --- | --- |
| [task-router](task-router/SKILL.md) | 读画像 → 消歧 → 定严谨度 → 选路由 → 出契约 → 复述确认 | task_contract、routing_decision、open_questions |
| [preference-distillation](preference-distillation/SKILL.md) | 从交互里归纳**稳定**偏好写回 `_profile`，区分一次性要求 | profile_update |

## 约束

- 不产出领域产物。写代码、写论文、做分析都不在这里发生。
- 不猜敏感身份属性（健康、宗教、族裔、性取向），除非用户主动说明且与任务直接相关。
- 契约没被确认时，下游产物必须标注「未确认前提下的草案」，不能当定稿交付。
