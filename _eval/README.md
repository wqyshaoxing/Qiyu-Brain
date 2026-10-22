# _eval

技能的回归样例。没有样例的「完整」只是文件齐全。

## 每个技能至少三件

1. **fixture**：一份最小但真实的输入（合成数据，不含真实论文、客户代码、健康记录）。
2. **expected**：期望产物的结构断言 + 1–2 条语义断言（例如「evidence_map 里每条 claim 都有 source_id」）。
3. **failure case**：一个必须被拒绝的场景（缺证据、来源不可达、版本不符），期望结果是 `blocked` 或 `failed`，**不是**生成占位产物。

## 目录

```text
_eval/<skill-name>/
├─ fixture/
├─ expected.json
└─ fail-case/
```

## 跑

```text
python scripts/validate.py
python -m unittest discover -s _eval -p "test_*.py"
```

校验只保证结构与契约一致。语义是否正确、图是否好看、翻译是否忠实，必须人工或由具备上下文的 agent 复核——退出码零不等于做对。

## 公开

`_eval` 里的样例默认允许公开。涉及真实数据时，脱敏后再放，且保留一条说明「这是脱敏数据」的 README。
