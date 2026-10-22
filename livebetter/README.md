# livebetter

生活事务。里面跑**两条不同的轨道**，风险类型不同，所以契约也分开写。

| 轨道 | 回答什么 | 主要风险 | 契约 |
| --- | --- | --- | --- |
| 健康 | 该不该做、怎么做、什么时候停 | 人身安全 | 免责 + 红旗优先 + 不碰药物剂量 |
| 事务 | 怎么办、依据是什么、消息可不可信 | 错误信息与被误导 | 来源分层 + 时效地域 + 不表态不预测 |

两条轨道不共用技能，只共用入口 `gateway-router`。

## 技能

| 轨道 | 阶段 | 技能 | 一句话 |
| --- | --- | --- | --- |
| 健康 | input | [livebetter-context-intake](input/livebetter-context-intake/SKILL.md) | 目标可观察、基线可计数；红旗先问，命中即转就医 |
| 健康 | output | [livebetter-plan-draft](output/livebetter-plan-draft/SKILL.md) | 半量起步、有递增规则、有停止条件、有复查日期 |
| 健康 | verify | [livebetter-red-flag-check](verify/livebetter-red-flag-check/SKILL.md) | 交付前重筛急症与禁忌，缺停止条件就拦下 |
| 事务 | input | [livebetter-legal-basis](input/livebetter-legal-basis/SKILL.md) | 找到并逐字引用条文：条号、生效日期、地域 |
| 事务 | input | [livebetter-policy-lookup](input/livebetter-policy-lookup/SKILL.md) | 找到政策原文：文号、印发/生效日期、适用对象、地方细则 |
| 事务 | reasoning | [livebetter-commonsense-check](reasoning/livebetter-commonsense-check/SKILL.md) | 这是规定、习惯、过时说还是传言？给五选一结论 |
| 事务 | output | [livebetter-playbook](output/livebetter-playbook/SKILL.md) | 前置条件 → 分步攻略 → 失败分支 → 可执行清单 |
| 事务 | output | [livebetter-briefing](output/livebetter-briefing/SKILL.md) | 时政与商业简报：事实/表态/解读/未证实四类分开 |

## 健康轨契约（不可协商）

1. **不是医疗建议**。每份产物开头必须有一行免责声明，且不得使用确定性诊断表述。
2. **红旗优先**。出现急症指征时，唯一正确输出是「立即就医」，停止后续所有建议。
3. **证据分级独立**。不照搬学术论文的证据分级；必须标注发布日期——健康领域过时结论危害最大。
4. **不替代个体化评估**。涉及药物相互作用、剂量、孕期、儿童、基础病时，必须指向持证医师。
5. **不编造来源**。查不到就写查不到，不许用「研究表明」兜底。

## 事务轨契约（不可协商）

1. **不是法律意见、不是投资建议**。只给条文、条件与渠道，不预测结果。
2. **来源分层**：官方原文 / 主流报道 / 行业媒体 / 未证实，四类必须分开标注，不得混写。
3. **时效与地域**：每条都带日期与适用地域；过期条文、失效政策不得当作现行。
4. **不表态不预测**：不评价政治立场，不给涨跌判断，不给「谁赢谁输」。
5. **查不到就说查不到**。不用「一般来说」「据了解」填补空白。

## 隐私

健康记录、检查结果、用药、住址、证件号属于高敏数据：默认只在本机工作区处理，`_memory` 只保留可公开复述的一般性结论。
