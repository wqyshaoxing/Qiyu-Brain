# 云端 Web API 配置、入库与恢复

默认 `import` 直接连接 `https://api.zotero.org`，不要求启动 Zotero Desktop。`import-desktop` 是显式选择的旧 Connector 路径。两种适配器使用不同 manifest，不能混用。云端文件保存到 Zotero Storage；WebDAV 不在此适配器范围内。

## 首次配置

通过运行入口首次执行本技能的 doctor、prepare 或动作时，会自动请求默认浏览器打开自带的 `onboarding.html`。页面包含 MinerU、Zotero 的注册、申请 key、系统环境变量与验证步骤；没有凭据表单。再次打开使用 `python <runtime> setup --workspace <work>`。独立安装包同样携带此页；浏览器打不开时会返回文件位置。`--plan` 不启动浏览器，不调用云端。

在官网创建私人 key，赋予目标库实际需要的读写与文件编辑权限。将以下值存入大写的持久系统环境变量，然后完全重启终端及 agent，使新进程继承变量：

| 名称 | 内容 |
| --- | --- |
| `ZOTERO_API_KEY` | 专用于此工作流的 Zotero 私人 key |
| `ZOTERO_LIBRARY_ID` | 个人库的数字 User ID；群组库则是数字 Group ID |
| `MINERU_API_KEY` | 后续文献提取用的 MinerU Token；云端入库本身不需要它 |

个人库默认 `zotero.library_type=user`。群组库在工作区 `.boomskills/config.json` 中设置为 `group`。此文件只记录变量名和非密钥设置；不能把 key 直接放进去。默认变量名也可在私有配置中设置为另一个大写名称。显式 `--library-id`、`--library-type` 可覆盖本次目标；目标 ID 是账号设置中的数字，不是用户名、显示名或桌面 collection ID。

凭据只放在官方 API 的请求头中，文件存储请求不会带 Zotero key。私有 key 文件仅作为已知环境不能传递变量时的显式兼容路径 `--api-key-file`，不作为新用户默认流程。不要将 key 放进 URL、参数值或公开日志。

安装 PDF 校验依赖：`python -m pip install pypdf`。`doctor` 只检查变量存在、ID 合法及本地依赖；执行 `check` 才验证云端读取，写入和文件权限由实际归档核验。无图形环境添加 `--no-open-guide`，或使用 `BOOMSKILLS_NO_BROWSER=1`。

## 命令

仓库入口为 `scripts/boomskills.py`，独立安装入口为 `<skill-dir>/_runtime/boomskills.py`，以下统一写作 `<runtime>`。

```text
python <runtime> doctor --workspace <work> --skill zotero-batch-pdf-import
python <runtime> run --workspace <work> --skill zotero-batch-pdf-import --action check --allow-external
python <runtime> run --workspace <work> --skill zotero-batch-pdf-import --action import --allow-external -- --source inputs/pdfs --batch-id 202610041200 --dry-run --out outputs/zotero-plan
python <runtime> run --workspace <work> --skill zotero-batch-pdf-import --action import --allow-external -- --source inputs/pdfs --batch-id 202610041200 --yes --out outputs/zotero-attempt-1
```

替换示例批次时间戳，并为每次 `--out` 选择一个不存在的新目录。`--dry-run` 严格解析本地 PDF，但不发任何云端请求、不修改持久 manifest，也不需要 key；此计划不证明云端目标或权限已验证。真正写入必须提供 `--yes`。默认 collection 名称为 `BoomSkills <batch-id>`，可用 `--collection-prefix` 改前缀，`--parent-collection <key>` 指定父 collection，或 `--collection-key <key>` 明确使用已有 collection。

每次结果产生 `import-result.json` 和 `import-report.md`。未指定 `--out` 的写入将结果放到私有 manifest 旁的 `batches/<attempt-id>/`，结果文件不会互相覆盖。运行入口另保留 action 日志。默认 manifest 是 PDF 源目录的 `.boomskills/zotero-web-manifest.json`；可通过 `--manifest` 指定另一个私有位置。它保存技术 library ID、云端对象 key、PDF 校验、元数据指纹及历史事件，应保留在本机且不要作为公开交付物上传。

## 已核验的书目信息

云端适配器没有桌面 PDF 自动识别。没有 `--metadata` 时归档为独立 PDF，`metadata_status=pending`。提供元数据可创建书目父条目和 PDF 子附件。不要从文件名猜 DOI、作者或发表状态；先由 Codex 核对提供者记录和论文。

元数据文件示例（合成示例，不代表真实论文）：

```json
{
  "papers": [
    {
      "file": "paper.pdf",
      "data": {
        "itemType": "journalArticle",
        "title": "Synthetic metadata example",
        "creators": [{"creatorType": "author", "name": "Example Research Group"}],
        "date": "2026"
      },
      "provenance": "Synthetic example; replace with the verified record source and review basis"
    }
  ]
}
```

`file` 相对于 `--source` 文件夹；源是单个 PDF 时相对于该文件的父目录。每项必须有 title、合法书目 itemType 与 provenance；字段按实际 Zotero 模板校验。元数据不能指定 key、version、collection 或 tag，防止绕过目标契约。调用时追加 `--metadata inputs/metadata.json`。云端父条目的已提供字段会与输入逐项核对；缺失字段不凭空补齐。先前独立附件的 metadata pending 不会通过创建第二份附件来解决，需要单独核验后的元数据迁移。

## 完成与恢复

每个 PDF 使用 SHA-256 内容标识；附件保存 `boomskills:sha256:<hash>` 标签，跨 manifest 可核对同一内容。上传后的服务器 MD5、PDF 内容类型、collection 归属和 batch 标签会读回核验。书目父条目属于 collection；子附件通过父条目归属，避免把 child collection 写成不合法结构。已有标签和其他 collection 均保留，更新使用服务器当前版本；冲突不会强行覆盖。

创建前先保存随机对象 key 与写入 token；上传按授权、存储 POST、登记依次执行，状态事件随每一步持久保存。中断后使用相同 library、批次 ID、manifest、元数据输入与 collection 策略重试，先核对保存的云端 key 或内容标签，再续传。历史 attempt 不会被后次尝试改写。OS 锁防止同一 manifest 并发写入，进程退出会释放锁。

HTTP 403 检查 key/目标库/权限，413 检查 Zotero Storage 额度，429 按服务端退避等待，412 或不同内容的 MD5 必须先处理冲突。较长退避会记录需要等待，不无限阻塞。只自动重试有界读取，写入失败依靠原 key 核对后恢复。不得删掉部分入库的条目或丢弃 manifest 来伪装成功；多个内容标签匹配、目标被删除、元数据变化等歧义保持未解决并报告。

完成报告必须披露 invalid、failed、partial、metadata pending 与未处理项。只有 `imported` 中明确标记云端核验通过的文件可计为成功；离线计划、read probe、脚本退出成功都不等于整个研究流程完成。结果还须按 [runtime.md](runtime.md) 提交与当前文件哈希绑定的审查记录。

官方参考：[账号注册](https://www.zotero.org/user/register/)、[API Keys](https://www.zotero.org/settings/keys)、[Web API v3](https://www.zotero.org/support/dev/web_api/v3/basics)、[条目与 collection 写入](https://www.zotero.org/support/dev/web_api/v3/write_requests)、[文件上传](https://www.zotero.org/support/dev/web_api/v3/file_upload)、[MinerU 官网](https://mineru.net/)、[MinerU API](https://mineru.net/apiManage/docs)。
