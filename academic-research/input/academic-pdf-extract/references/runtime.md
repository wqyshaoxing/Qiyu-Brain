# mineru-pdf-to-markdown 运行闭环

## 安装与配置

从仓库根目录执行 `python scripts/boomskills.py install --dest <skills-root> --skill mineru-pdf-to-markdown`。安装器会把本技能及必需运行脚本复制为独立包；现有同名包默认不覆盖。宿主重新加载技能后可直接调用 `$mineru-pdf-to-markdown`。

仓库中使用 `python scripts/boomskills.py`；已安装技能使用 `python <skill-dir>/_runtime/boomskills.py`，以下以 `<runtime>` 表示该入口。Python 3.11+ 即可使用基础运行层。详细工具配置在仓库 `docs/dependencies.md`，安装包中位于 `_runtime/dependencies.md`。

```text
python <runtime> init --workspace <work>
python <runtime> doctor --skill mineru-pdf-to-markdown --workspace <work>
```

配置保存在工作区私有 `.boomskills/config.json`；只填写程序、端点和环境变量名称，凭据通过环境变量传入。doctor 的 available 只表示该依赖检查通过；host_check_required/unverified 需要在宿主中或通过显式在线探测核验。服务探测可追加 `--online`。

首次使用会自动在浏览器打开自带说明页，包含 MinerU 官网注册、API Token 创建和系统环境变量设置，也附 Zotero 注册/key 入口。默认使用大写的持久系统变量 `MINERU_API_KEY`；设置后完全重启终端和 agent。`python <runtime> setup --workspace <work>` 再次打开；无图形环境使用 `--no-open-guide`，依赖仍会正常检查，缺失时保持 blocked。

## 动作与交接

| 动作 | 实际影响 | 退出成功意味着 |
| --- | --- | --- |
| `convert` | 将明确选择的 PDF 上传 MinerU，保存 full.md 与资源 | 提取请求成功并保存结果；需核验文字、公式和图片 |

```text
python <runtime> run --skill mineru-pdf-to-markdown --workspace <work> --action convert --allow-external -- inputs/paper.pdf
```

先追加 `--plan` 查看依赖与命令；该参数必须放在透传分隔符 `--` 前。有外部效应的动作需要 `--allow-external`；具体写入还沿用脚本的 `--yes`/`--apply` 开关。当前任务已授权的范围不必重复询问。

需要宿主继续完成的内容，用以下命令创建可追踪交接。已有输入使用工作区相对路径，并可重复传入 `--input`：

```text
python <runtime> prepare --skill mineru-pdf-to-markdown --workspace <work> --task "描述本次任务和交付范围"
python <runtime> status --workspace <work>
```

读取返回的 `task.md`，执行本技能并检查实际输出。prepare 的状态是 awaiting_agent，脚本成功是 action_succeeded，两者都不会冒充整个技能已完成。

## 验收与恢复

核对 full.md 与图片资源；提取源文件只读，重复运行默认跳过完整结果。

必须提供以下 artifact roles：`full_md`、`extraction_report`。具体类型和说明见同目录 `runtime.json`。完成实际检查后创建 `review.json`：

```json
{
  "passed": true,
  "checks": ["写明实际执行且通过的检查，不能用模板文字代替"],
  "limitations": [],
  "artifact_sha256": {"<role>": "对应文件的当前 SHA-256"}
}
```

执行 `finish --workspace <work> --run <run-id> --artifact <role>=<relative-file>`，为每个必需 role 追加一个 `--artifact`，最后加 `--review review.json`。只有文件校验、完整角色与当前哈希绑定的审查记录均通过才记录 completed。结构校验不代替科学或视觉判断。

恢复：保留 PDF 和提取任务信息；恢复令牌/网络后重试。不要用覆盖完整 full.md 的方式重试分析。 每次执行生成新的 run-id，日志保存在 `.boomskills/runs/`，不会覆盖前次尝试。生成产物仍保存在用户选定位置；运行记录目录默认不进入 Git。
