# zotero-batch-pdf-import 运行闭环

## 安装与配置

从仓库根目录执行 `python scripts/boomskills.py install --dest <skills-root> --skill zotero-batch-pdf-import`。安装器会把本技能及必需运行脚本复制为独立包；现有同名包默认不覆盖。宿主重新加载技能后可直接调用 `$zotero-batch-pdf-import`。

仓库中使用 `python scripts/boomskills.py`；已安装技能使用 `python <skill-dir>/_runtime/boomskills.py`，以下以 `<runtime>` 表示该入口。Python 3.11+ 即可使用基础运行层。详细工具配置在仓库 `docs/dependencies.md`，安装包中位于 `_runtime/dependencies.md`。

```text
python <runtime> init --workspace <work>
python <runtime> doctor --skill zotero-batch-pdf-import --workspace <work>
```

配置保存在工作区私有 `.boomskills/config.json`；只填写程序、端点和环境变量名称，凭据通过环境变量传入。doctor 的 available 只表示该依赖检查通过；host_check_required/unverified 需要在宿主中或通过显式在线探测核验。服务探测可追加 `--online`。

首次使用自动用浏览器打开账号/key/系统环境变量说明页；`setup --workspace <work>` 再次打开。使用 `ZOTERO_API_KEY`、`ZOTERO_LIBRARY_ID`；个人库默认 user，群组库设置 group。更改环境变量后完全重启终端与 agent。详见 [云端配置与恢复](web-api.md)。

## 动作与交接

| 动作 | 实际影响 | 退出成功意味着 |
| --- | --- | --- |
| `import` | 默认离线 PDF 校验；--yes 创建/复用云端时间戳 collection 并上传选定 PDF | 逐文件云端核验；缺书目信息的条目仍为 metadata pending |
| `check` | 仅通过官方 HTTPS API 检查读取权限 | 读取已验证；写入/文件权限未验证 |
| `import-desktop` | 旧 Connector 路径，--yes 写入已有选定目标并请求识别 | 需核验桌面端目标、识别结果与标签 |

```text
python <runtime> run --skill zotero-batch-pdf-import --workspace <work> --action import --allow-external -- --source inputs/pdfs --dry-run
```

先追加 `--plan` 查看依赖与命令；该参数必须放在透传分隔符 `--` 前。有外部效应的动作需要 `--allow-external`；具体写入还沿用脚本的 `--yes`/`--apply` 开关。当前任务已授权的范围不必重复询问。

需要宿主继续完成的内容，用以下命令创建可追踪交接。已有输入使用工作区相对路径，并可重复传入 `--input`：

```text
python <runtime> prepare --skill zotero-batch-pdf-import --workspace <work> --task "描述本次任务和交付范围"
python <runtime> status --workspace <work>
```

读取返回的 `task.md`，执行本技能并检查实际输出。prepare 的状态是 awaiting_agent，脚本成功是 action_succeeded，两者都不会冒充整个技能已完成。

## 验收与恢复

核对云端真实 collection、附件 MD5、PDF 校验、父条目归属与批次标签。元数据来自显式核验输入；缺失时标为 pending，不能声称自动识别完成。核对 failed/partial/未解决项，按请求范围判断是否满足交付要求。

必须提供以下 artifact roles：`import_result`、`import_report`。具体类型和说明见同目录 `runtime.json`。完成实际检查后创建 `review.json`：

```json
{
  "passed": true,
  "checks": ["写明实际执行且通过的检查，不能用模板文字代替"],
  "limitations": [],
  "artifact_sha256": {"<role>": "对应文件的当前 SHA-256"}
}
```

执行 `finish --workspace <work> --run <run-id> --artifact <role>=<relative-file>`，为每个必需 role 追加一个 `--artifact`，最后加 `--review review.json`。只有文件校验、完整角色与当前哈希绑定的审查记录均通过才记录 completed。结构校验不代替科学或视觉判断。

恢复：保留原 cloud manifest、批次、library 与元数据；先按已保存对象 key/内容标签核对再续传，保留每次状态事件。不要通过丢弃 manifest 或重复创建来绕过部分失败。每次运行生成新 run-id，日志保存在 `.boomskills/runs/`；结果输出目录也必须使用新的名字。
