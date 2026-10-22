# qiyu-brain (DSH plugin)

把 Qiyu-Brain 的技能作为一个 DeepSeek Harness 插件提供。

## 它做什么

在 `apply()` 里向 `ctx.skills` 注册一个名为 `qiyu-brain` 的 provider，把本包 `skills/` 下的每个 `<name>/SKILL.md` 变成技能目录条目。技能正文按需读取，不预加载。

插件本身**零运行时依赖**：只用 `node:fs` / `node:path` / `node:url`，自己解析 frontmatter。原因是宿主 profile 解析不到应用私有的 `@deepseek-ai/schemastery`、`yaml`、`dsh-skill`。

## 安装

两种方式，任选其一：

1. **插件管理器（推荐）**：设置 → 插件 → 从本地目录安装，指向本目录。
2. **手工安装到 profile**：

```text
copy 这个目录 → <DSH_HOME>/profiles/<profile>/node_modules/qiyu-brain
```

然后在同目录的 `cordis.patch.yml` 追加：

```yaml
- id: qiyu-brain
  name: "qiyu-brain"
  config:
    skillsDir: "C:/绝对路径/.../skills"   # 可省略，默认用包内 skills/
```

重启 DSH 生效。插件列表里应出现 `qiyu-brain`。

## 配置

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `skillsDir` | 包内 `skills/` | 技能根目录，必须绝对路径 |

## 失败行为

设计上**不会因为自身问题拖垮宿主**：

- `import` 阶段不读磁盘，只定义常量。
- `apply()` 内包住发现逻辑；目录不存在或单个技能 frontmatter 损坏，只 `console.warn` 并在目录里跳过该技能。
- provider 的 `list()` 恒返回数组，`get()` 才会真正读文件。

## 与散装技能的区别

散装是把 N 个目录塞进技能根，没有版本、没有开关、卸载靠删目录。插件是一个包：版本可管理、可整体启停、可卸载。技能内容仍是 `SKILL.md` 目录（这是 DSH 的格式要求），但作为一个单元发布。

**不要同时装两份**：插件与 `.dsh/skills/` 下的散装副本会注册同名技能，最终由 rank 决定谁生效（散装的 project 根 rank 更低，会赢），行为容易让人困惑。
